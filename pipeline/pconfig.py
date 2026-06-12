"""Pipeline configuration loaded from environment / .env file.

Kept separate from the bot's ``config.py`` so the pipeline can run as a
standalone CLI (without a Telegram token) and vice-versa.
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

# --- Orchestrator (Claude) -------------------------------------------------
ANTHROPIC_API_KEY = _get("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = _get("ANTHROPIC_MODEL", "claude-opus-4-8")

# --- Research: ScrapeCreators ---------------------------------------------
SCRAPECREATORS_API_KEY = _get("SCRAPECREATORS_API_KEY")
SCRAPECREATORS_BASE_URL = _get(
    "SCRAPECREATORS_BASE_URL", "https://api.scrapecreators.com"
)

# --- Video analysis: Gemini Flash Lite ------------------------------------
GEMINI_API_KEY = _get("GEMINI_API_KEY")
GEMINI_MODEL = _get("GEMINI_MODEL", "gemini-2.5-flash-lite")

# --- Generation: Higgsfield (Nano Banana first frame + Kling animate) ------
HIGGSFIELD_API_KEY = _get("HIGGSFIELD_API_KEY")
HIGGSFIELD_BASE_URL = _get("HIGGSFIELD_BASE_URL", "https://api.higgsfield.ai")
FIRST_FRAME_MODEL = _get("FIRST_FRAME_MODEL", "nano-banana")
ANIMATE_MODEL = _get("ANIMATE_MODEL", "kling")

# --- Subtitles (reuse the existing Remotion renderer) ----------------------
SUBTITLE_PRESET = _get("PIPELINE_SUBTITLE_PRESET", "hormozi")
RENDER_SUBTITLES = _flag("PIPELINE_RENDER_SUBTITLES", not DRY_RUN)

# --- Analytics alerts ------------------------------------------------------
ALERT_BOT_TOKEN = _get("ALERT_BOT_TOKEN") or _get("BOT_TOKEN")
ALERT_CHAT_ID = _get("ALERT_CHAT_ID")


def ensure_dirs() -> None:
    for path in (WORKSPACE, CHARACTERS_DIR, RUNS_DIR):
        path.mkdir(parents=True, exist_ok=True)
