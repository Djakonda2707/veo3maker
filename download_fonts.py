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
    # Inter is a variable font in google/fonts; libass picks it up fine.
    "Inter.ttf": f"{BASE}/inter/Inter%5Bopsz%2Cwght%5D.ttf",
    "Inter-Italic.ttf": f"{BASE}/inter/Inter-Italic%5Bopsz%2Cwght%5D.ttf",
    "Anton-Regular.ttf": f"{BASE}/anton/Anton-Regular.ttf",
    "BebasNeue-Regular.ttf": f"{BASE}/bebasneue/BebasNeue-Regular.ttf",
    "PlayfairDisplay.ttf": f"{BASE}/playfairdisplay/PlayfairDisplay%5Bwght%5D.ttf",
    "PlayfairDisplay-Italic.ttf": (
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
