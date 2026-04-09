"""Configuration loaded from environment / .env file."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _get(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value


REPO_ROOT = Path(__file__).parent
TMP_ROOT = REPO_ROOT / "tmp"

# --- Remotion --------------------------------------------------------------
REMOTION_ROOT = REPO_ROOT / "remotion"

BOT_TOKEN = _get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set. Put it into .env")

# --- Whisper ---------------------------------------------------------------
WHISPER_MODEL = _get("WHISPER_MODEL", "small")
WHISPER_DEVICE = _get("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = _get("WHISPER_COMPUTE_TYPE", "int8")
WHISPER_LANGUAGE = _get("WHISPER_LANGUAGE")  # None -> auto-detect

# --- Limits ----------------------------------------------------------------
MAX_VIDEO_SIZE_MB = int(_get("MAX_VIDEO_SIZE_MB", "20"))
