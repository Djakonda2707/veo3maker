"""Telegram bot: dynamic burned-in subtitles with preset picker."""
import asyncio
import logging
import shutil
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatAction, ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, FSInputFile, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

import config
from presets import PRESET_BY_KEY, PRESETS
from preview import PREVIEW_GRID_PATH, ensure_previews
from render import FFmpegError, burn_subtitles, extract_audio, probe_size
from subtitles import build_ass
from transcribe import transcribe_audio

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("subsbot")

bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher(storage=MemoryStorage())


class VideoStates(StatesGroup):
    choosing_style = State()


WELCOME = (
    "Привет! Пришли мне видео — я наложу динамические встроенные субтитры.\n\n"
    "После загрузки ты выберешь стиль из <b>6 пресетов</b> "
    "(превью покажу картинкой).\n\n"
    f"Лимит файла: <b>{config.MAX_VIDEO_SIZE_MB} МБ</b> "
    "(ограничение Telegram Bot API)."
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _is_video_message(message: Message) -> bool:
    if message.video or message.video_note:
        return True
    if message.document and (message.document.mime_type or "").startswith("video/"):
        return True
    return False


def _build_presets_keyboard():
    kb = InlineKeyboardBuilder()
    for preset in PRESETS:
        kb.button(text=preset.title, callback_data=f"style:{preset.key}")
    kb.button(text="✖ Отмена", callback_data="style:cancel")
    kb.adjust(2, 2, 2, 1)
    return kb.as_markup()


def _tail(text: str, limit: int = 600) -> str:
    text = text.strip()
    return text if len(text) <= limit else "..." + text[-limit:]


async def _cleanup(work_dir: Path | str | None) -> None:
    if not work_dir:
        return
    shutil.rmtree(Path(work_dir), ignore_errors=True)


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await _cleanup(data.get("work_dir"))
    await state.clear()
    await message.answer(WELCOME)


@dp.message(Command("help"))
async def cmd_help(message: Message) -> None:
    lines = ["Пресеты субтитров:"]
    for p in PRESETS:
        lines.append(f"• <b>{p.title}</b>")
    lines.append(
        "\nПришли видео — после загрузки я покажу витрину "
        "и предложу выбрать стиль."
    )
    await message.answer("\n".join(lines))


@dp.message(F.video | F.video_note | F.document)
async def handle_video(message: Message, state: FSMContext) -> None:
    if not _is_video_message(message):
        await message.answer("Пришли, пожалуйста, именно видео-файл.")
        return

    file_obj = message.video or message.video_note or message.document
    if (
        file_obj.file_size
        and file_obj.file_size > config.MAX_VIDEO_SIZE_MB * 1024 * 1024
    ):
        await message.answer(
            f"Файл больше {config.MAX_VIDEO_SIZE_MB} МБ — Telegram Bot API "
            "не даст его скачать. Сожми или подними local Bot API server."
        )
        return

    # Clear any previous in-progress state from the same user.
    prev = await state.get_data()
    await _cleanup(prev.get("work_dir"))
    await state.clear()

    status = await message.answer("Скачиваю видео...")

    work_dir = config.TMP_ROOT / f"{message.from_user.id}_{message.message_id}"
    work_dir.mkdir(parents=True, exist_ok=True)
    input_path = work_dir / "input.mp4"

    try:
        await bot.download(file_obj, destination=input_path)
    except Exception as exc:
        logger.exception("download failed")
        await status.edit_text(f"Не удалось скачать: {exc}")
        await _cleanup(work_dir)
        return

    await state.set_state(VideoStates.choosing_style)
    await state.update_data(
        work_dir=str(work_dir),
        input_path=str(input_path),
    )

    await status.delete()
    await message.answer_photo(
        FSInputFile(PREVIEW_GRID_PATH),
        caption="Выбери стиль субтитров:",
        reply_markup=_build_presets_keyboard(),
    )


@dp.callback_query(F.data.startswith("style:"))
async def on_style(callback: CallbackQuery, state: FSMContext) -> None:
    key = callback.data.split(":", 1)[1]

    if key == "cancel":
        data = await state.get_data()
        await _cleanup(data.get("work_dir"))
        await state.clear()
        await callback.answer("Отменено")
        try:
            await callback.message.delete()
        except Exception:
            pass
        return

    current_state = await state.get_state()
    if current_state != VideoStates.choosing_style.state:
        await callback.answer("Сначала пришли видео", show_alert=True)
        return

    preset = PRESET_BY_KEY.get(key)
    if not preset:
        await callback.answer("Неизвестный стиль")
        return

    data = await state.get_data()
    work_dir = Path(data["work_dir"])
    input_path = Path(data["input_path"])
    if not input_path.exists():
        await callback.answer("Видео пропало, пришли заново", show_alert=True)
        await state.clear()
        return

    await callback.answer(f"Стиль: {preset.title}")
    try:
        await callback.message.edit_caption(
            caption=f"Стиль: <b>{preset.title}</b>\nОбрабатываю..."
        )
    except Exception:
        pass
    # Lock: drop state so double-clicks don't fire a second pipeline on the
    # same working directory.
    await state.clear()

    audio_path = work_dir / "audio.wav"
    subs_path = work_dir / "subs.ass"
    output_path = work_dir / "output.mp4"

    try:
        await extract_audio(input_path, audio_path)

        words, language = await asyncio.to_thread(
            transcribe_audio,
            str(audio_path),
            config.WHISPER_MODEL,
            config.WHISPER_DEVICE,
            config.WHISPER_COMPUTE_TYPE,
            config.WHISPER_LANGUAGE,
        )
        if not words:
            await callback.message.answer("Не удалось распознать речь в видео.")
            return

        width, height = await probe_size(input_path)
        ass_content = build_ass(words, width, height, preset)
        subs_path.write_text(ass_content, encoding="utf-8")

        await bot.send_chat_action(
            callback.message.chat.id, ChatAction.UPLOAD_VIDEO
        )
        await burn_subtitles(
            input_path, subs_path, output_path, fonts_dir=config.FONTS_DIR
        )

        await callback.message.answer_video(
            FSInputFile(output_path),
            caption=f"Готово · <b>{preset.title}</b> · язык: <b>{language}</b>",
            supports_streaming=True,
        )
        try:
            await callback.message.delete()
        except Exception:
            pass

    except FFmpegError as exc:
        logger.exception("ffmpeg failed")
        await callback.message.answer(
            f"Ошибка ffmpeg:\n<pre>{_tail(str(exc))}</pre>"
        )
    except Exception as exc:
        logger.exception("processing failed")
        await callback.message.answer(f"Ошибка: {exc}")
    finally:
        await _cleanup(work_dir)


@dp.message()
async def fallback(message: Message) -> None:
    await message.answer("Пришли мне видео — я наложу на него субтитры.")


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
async def _startup() -> None:
    config.TMP_ROOT.mkdir(parents=True, exist_ok=True)
    # Wipe any leftovers from a previous run.
    for child in config.TMP_ROOT.iterdir():
        if child.is_dir():
            shutil.rmtree(child, ignore_errors=True)

    if config.AUTO_DOWNLOAD_FONTS:
        try:
            from download_fonts import download_all

            await asyncio.to_thread(download_all, False)
        except Exception as exc:
            logger.warning("font download failed: %s", exc)

    logger.info("Generating preset previews...")
    try:
        await ensure_previews()
    except Exception:
        logger.exception("preview generation failed")


async def main() -> None:
    await _startup()
    logger.info(
        "Starting bot, whisper=%s device=%s",
        config.WHISPER_MODEL,
        config.WHISPER_DEVICE,
    )
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
