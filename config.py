"""Configuration loaded from environment / .env file."""
import os

from dotenv import load_dotenv

load_dotenv()


def _get(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value


BOT_TOKEN = _get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set. Put it into .env")

# --- Whisper ---------------------------------------------------------------
WHISPER_MODEL = _get("WHISPER_MODEL", "small")
WHISPER_DEVICE = _get("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = _get("WHISPER_COMPUTE_TYPE", "int8")
WHISPER_LANGUAGE = _get("WHISPER_LANGUAGE")  # None -> auto-detect

# --- Subtitles appearance --------------------------------------------------
SUB_FONT = _get("SUB_FONT", "Arial")
SUB_FONT_SIZE_RATIO = float(_get("SUB_FONT_SIZE_RATIO", "0.075"))
SUB_MAX_WORDS = int(_get("SUB_MAX_WORDS", "3"))
SUB_POSITION = _get("SUB_POSITION", "bottom")
SUB_HIGHLIGHT_COLOR = _get("SUB_HIGHLIGHT_COLOR", "&H0000FFFF&")

# --- Limits ----------------------------------------------------------------
MAX_VIDEO_SIZE_MB = int(_get("MAX_VIDEO_SIZE_MB", "20"))
