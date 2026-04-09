"""Telegram bot that burns dynamic per-word subtitles into uploaded videos."""
import asyncio
import logging
import tempfile
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatAction, ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import FSInputFile, Message

import config
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
dp = Dispatcher()


WELCOME = (
    "Привет! Пришли мне видео — верну его с динамическими "
    "встроенными субтитрами (подсветка слова под TikTok / Reels).\n\n"
    f"Ограничение размера: <b>{config.MAX_VIDEO_SIZE_MB} МБ</b> "
    "(лимит Telegram Bot API)."
)


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(WELCOME)


@dp.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "Отправь видеосообщение или файл. Я:\n"
        "1) извлеку аудио\n"
        "2) распознаю речь с пословной разметкой (Whisper)\n"
        "3) сгенерирую анимированные ASS-субтитры\n"
        "4) выжгу их поверх видео через ffmpeg\n"
        "5) верну результат"
    )


def _is_video_message(message: Message) -> bool:
    if message.video or message.video_note:
        return True
    if message.document and (message.document.mime_type or "").startswith("video/"):
        return True
    return False


@dp.message(F.video | F.video_note | F.document)
async def handle_video(message: Message) -> None:
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
            "не даст его скачать. Сожми видео или подними local Bot API server."
        )
        return

    status = await message.answer("Скачиваю видео...")

    with tempfile.TemporaryDirectory(prefix="subsbot_") as tmpdir:
        tmp = Path(tmpdir)
        input_path = tmp / "input.mp4"
        audio_path = tmp / "audio.wav"
        subs_path = tmp / "subs.ass"
        output_path = tmp / "output.mp4"

        try:
            await bot.download(file_obj, destination=input_path)

            await status.edit_text("Извлекаю аудио...")
            await extract_audio(input_path, audio_path)

            await status.edit_text("Распознаю речь (Whisper)...")
            words, language = await asyncio.to_thread(
                transcribe_audio,
                str(audio_path),
                config.WHISPER_MODEL,
                config.WHISPER_DEVICE,
                config.WHISPER_COMPUTE_TYPE,
                config.WHISPER_LANGUAGE,
            )
            if not words:
                await status.edit_text("Не удалось распознать речь в видео.")
                return

            await status.edit_text("Генерирую субтитры...")
            width, height = await probe_size(input_path)
            font_size = max(24, int(height * config.SUB_FONT_SIZE_RATIO))
            ass_content = build_ass(
                words,
                play_res_x=width,
                play_res_y=height,
                font=config.SUB_FONT,
                font_size=font_size,
                max_words_per_phrase=config.SUB_MAX_WORDS,
                position=config.SUB_POSITION,
                highlight_color=config.SUB_HIGHLIGHT_COLOR,
            )
            subs_path.write_text(ass_content, encoding="utf-8")

            await status.edit_text("Наношу субтитры на видео...")
            await bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_VIDEO)
            await burn_subtitles(input_path, subs_path, output_path)

            await status.edit_text("Отправляю результат...")
            await message.answer_video(
                FSInputFile(output_path),
                caption=f"Готово. Язык: <b>{language}</b>",
                supports_streaming=True,
            )
            await status.delete()

        except FFmpegError as exc:
            logger.exception("ffmpeg failed")
            await _safe_edit(
                status, f"Ошибка ffmpeg:\n<pre>{_tail(str(exc))}</pre>"
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("processing failed")
            await _safe_edit(status, f"Ошибка: {exc}")


async def _safe_edit(message: Message, text: str) -> None:
    try:
        await message.edit_text(text)
    except Exception:
        logger.exception("failed to edit status message")


def _tail(text: str, limit: int = 500) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return "..." + text[-limit:]


@dp.message()
async def fallback(message: Message) -> None:
    await message.answer("Пришли мне видео — я наложу на него субтитры.")


async def main() -> None:
    logger.info("Starting bot, whisper=%s device=%s", config.WHISPER_MODEL, config.WHISPER_DEVICE)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
