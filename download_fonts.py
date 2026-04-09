"""Download free OFL fonts used by the subtitle presets.

Run once: ``python download_fonts.py``. The bot also calls this on startup.
"""
import logging
import urllib.request
from pathlib import Path

logger = logging.getLogger(__name__)

FONTS_DIR = Path(__file__).parent / "fonts"
BASE = "https://github.com/google/fonts/raw/main/ofl"

FILES: dict[str, str] = {
    "Inter-Bold.ttf": f"{BASE}/inter/static/Inter-Bold.ttf",
    "Inter-Black.ttf": f"{BASE}/inter/static/Inter-Black.ttf",
    "Anton-Regular.ttf": f"{BASE}/anton/Anton-Regular.ttf",
    "BebasNeue-Regular.ttf": f"{BASE}/bebasneue/BebasNeue-Regular.ttf",
    "PlayfairDisplay-BlackItalic.ttf": (
        f"{BASE}/playfairdisplay/PlayfairDisplay%5Bwght%5D.ttf"
    ),
    "PlayfairDisplay-Italic-BlackItalic.ttf": (
        f"{BASE}/playfairdisplay/PlayfairDisplay-Italic%5Bwght%5D.ttf"
    ),
}


def download_all(verbose: bool = True) -> None:
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    for name, url in FILES.items():
        dest = FONTS_DIR / name
        if dest.exists() and dest.stat().st_size > 0:
            if verbose:
                print(f"skip  {name}")
            continue
        if verbose:
            print(f"fetch {name}")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp, open(dest, "wb") as f:
                f.write(resp.read())
        except Exception as exc:
            logger.warning("failed to download %s: %s", name, exc)
            if dest.exists():
                dest.unlink(missing_ok=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    download_all()
    print(f"Fonts directory: {FONTS_DIR}")
