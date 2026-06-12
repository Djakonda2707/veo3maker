"""Pipeline configuration loaded from environment / .env file.

Kept separate from the bot's ``config.py`` so the pipeline can run as a
standalone CLI (without a Telegram token) and vice-versa.

Stack (всё pluggable через .env):

* Оркестратор   — Claude Code (подписка), отдельный API-ключ не нужен.
* First frame   — Nano Banana / Gemini image через relay-совместимый
                  endpoint (laozhang.ai по умолчанию, или прямой Gemini).
* Оживление     — fal.ai (Wan 2.5 по умолчанию; Kling/Seedance флагом).
* Сборка        — ffmpeg. Субтитры — существующий Remotion-рендер.
* Скрейпер      — RapidAPI social-api4 (этап Research, позже).
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _get(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value


def _flag(name: str, default: bool) -> bool:
    value = _get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


REPO_ROOT = Path(__file__).resolve().parent.parent
PIPELINE_ROOT = REPO_ROOT / "pipeline"
REMOTION_ROOT = REPO_ROOT / "remotion"

# Where runs, characters and artifacts live. Git-ignored.
WORKSPACE = Path(_get("PIPELINE_WORKSPACE", str(REPO_ROOT / "workspace")))
CHARACTERS_DIR = WORKSPACE / "characters"
RUNS_DIR = WORKSPACE / "runs"

# Global kill-switch for real API calls. Defaults to ON so a fresh clone
# runs end-to-end with deterministic mock artifacts and zero spend.
DRY_RUN = _flag("PIPELINE_DRY_RUN", True)

# --- Output format ---------------------------------------------------------
VIDEO_WIDTH = int(_get("PIPELINE_VIDEO_WIDTH", "1080"))
VIDEO_HEIGHT = int(_get("PIPELINE_VIDEO_HEIGHT", "1920"))  # 9:16 vertical
FPS = int(_get("PIPELINE_FPS", "30"))
SEGMENT_SECONDS = float(_get("PIPELINE_SEGMENT_SECONDS", "10"))  # 10s "куски"

# --- First frame (image) ---------------------------------------------------
# Provider: "mock" | "relay" (OpenAI/Gemini-compatible, e.g. laozhang.ai) | "gemini"
IMAGE_PROVIDER = _get("IMAGE_PROVIDER", "mock")
IMAGE_API_KEY = _get("IMAGE_API_KEY")
# laozhang.ai exposes an OpenAI-compatible base; direct Google would be
# https://generativelanguage.googleapis.com/v1beta/openai
IMAGE_API_BASE_URL = _get("IMAGE_API_BASE_URL", "https://api.laozhang.ai/v1")
IMAGE_MODEL = _get("IMAGE_MODEL", "gemini-2.5-flash-image")  # Nano Banana

# --- Animate (image -> video) ----------------------------------------------
# Provider: "mock" | "fal" | "higgsfield"
VIDEO_PROVIDER = _get("VIDEO_PROVIDER", "mock")
FAL_API_KEY = _get("FAL_API_KEY")
# fal.ai model slug used for image-to-video. Wan 2.5 = cheap default.
FAL_VIDEO_MODEL = _get("FAL_VIDEO_MODEL", "fal-ai/wan-25/image-to-video")
HIGGSFIELD_API_KEY = _get("HIGGSFIELD_API_KEY")
HIGGSFIELD_BASE_URL = _get("HIGGSFIELD_BASE_URL", "https://api.higgsfield.ai")

# --- Research scraper (этап 1, позже) --------------------------------------
# Provider: "mock" | "rapidapi" | "scrapecreators"
SCRAPER_PROVIDER = _get("SCRAPER_PROVIDER", "mock")
RAPIDAPI_KEY = _get("RAPIDAPI_KEY")
RAPIDAPI_HOST = _get("RAPIDAPI_HOST", "social-api4.p.rapidapi.com")
SCRAPECREATORS_API_KEY = _get("SCRAPECREATORS_API_KEY")

# --- Video analysis: Gemini Flash Lite (этап 1, позже) ---------------------
GEMINI_API_KEY = _get("GEMINI_API_KEY") or IMAGE_API_KEY
GEMINI_BASE_URL = _get("GEMINI_BASE_URL", IMAGE_API_BASE_URL)
GEMINI_MODEL = _get("GEMINI_MODEL", "gemini-2.5-flash-lite")

# --- Subtitles (reuse the existing Remotion renderer) ----------------------
SUBTITLE_PRESET = _get("PIPELINE_SUBTITLE_PRESET", "hormozi")
RENDER_SUBTITLES = _flag("PIPELINE_RENDER_SUBTITLES", False)

# --- Analytics alerts (этап 1, позже) --------------------------------------
ALERT_BOT_TOKEN = _get("ALERT_BOT_TOKEN") or _get("BOT_TOKEN")
ALERT_CHAT_ID = _get("ALERT_CHAT_ID")


def ensure_dirs() -> None:
    for path in (WORKSPACE, CHARACTERS_DIR, RUNS_DIR):
        path.mkdir(parents=True, exist_ok=True)
