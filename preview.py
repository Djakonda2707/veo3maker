"""Pre-generate preset preview images shown in the bot picker."""
import asyncio
import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from presets import PRESETS, Preset
from render import render_subtitle_frame
from subtitles import build_ass

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).parent
PREVIEWS_DIR = REPO_ROOT / "previews"
FONTS_DIR = REPO_ROOT / "fonts"
PREVIEW_GRID_PATH = PREVIEWS_DIR / "grid.jpg"

PREVIEW_W = 1080
PREVIEW_H = 1920
# Sample word layout timing — first word active around 0.4s.
SAMPLE_T0 = 0.0
SAMPLE_STEP = 0.55
SAMPLE_WORD_DUR = 0.5
RENDER_TS = 0.4


def _sample_words(preset: Preset) -> list[dict]:
    raw = preset.sample_text.split()
    words: list[dict] = []
    t = SAMPLE_T0
    for w in raw:
        words.append({"text": w, "start": t, "end": t + SAMPLE_WORD_DUR})
        t += SAMPLE_STEP
    return words


async def _render_single(preset: Preset) -> Path:
    out_path = PREVIEWS_DIR / f"{preset.key}.png"
    if out_path.exists():
        return out_path

    words = _sample_words(preset)
    ass_content = build_ass(words, PREVIEW_W, PREVIEW_H, preset)
    ass_path = PREVIEWS_DIR / f"{preset.key}.ass"
    ass_path.write_text(ass_content, encoding="utf-8")

    try:
        await render_subtitle_frame(
            subs_path=ass_path,
            output_path=out_path,
            width=PREVIEW_W,
            height=PREVIEW_H,
            ts=RENDER_TS,
            fonts_dir=FONTS_DIR,
        )
    finally:
        ass_path.unlink(missing_ok=True)
    return out_path


_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "C:\\Windows\\Fonts\\arialbd.ttf",
]


def _load_label_font(size: int):
    for path in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _compose_grid(preview_paths: list[Path], titles: list[str], out_path: Path) -> None:
    cell_w, cell_h = 540, 960
    gap = 20
    header_h = 110
    cols, rows = 3, 2
    grid_w = cols * cell_w + (cols + 1) * gap
    grid_h = header_h + rows * cell_h + (rows + 1) * gap

    grid = Image.new("RGB", (grid_w, grid_h), (12, 12, 22))
    draw = ImageDraw.Draw(grid)

    title_font = _load_label_font(56)
    num_font = _load_label_font(72)

    draw.text(
        (grid_w // 2, header_h // 2),
        "Выбери стиль",
        font=title_font,
        fill=(255, 255, 255),
        anchor="mm",
    )

    for i, (p, _title) in enumerate(zip(preview_paths, titles)):
        img = Image.open(p).convert("RGB").resize((cell_w, cell_h), Image.LANCZOS)
        col = i % cols
        row = i // cols
        x = gap + col * (cell_w + gap)
        y = header_h + gap + row * (cell_h + gap)
        grid.paste(img, (x, y))

        # Draw the number badge in the top-left corner of the cell.
        num = str(i + 1)
        bbox = draw.textbbox((0, 0), num, font=num_font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        pad = 18
        bx0, by0 = x + 18, y + 18
        bx1, by1 = bx0 + tw + 2 * pad, by0 + th + 2 * pad
        try:
            draw.rounded_rectangle((bx0, by0, bx1, by1), radius=18, fill=(0, 0, 0))
        except AttributeError:  # pillow < 8.2
            draw.rectangle((bx0, by0, bx1, by1), fill=(0, 0, 0))
        draw.text(
            ((bx0 + bx1) // 2, (by0 + by1) // 2),
            num,
            font=num_font,
            fill=(255, 255, 255),
            anchor="mm",
        )

    grid.save(out_path, "JPEG", quality=88, optimize=True)


async def ensure_previews(force: bool = False) -> Path:
    """Make sure all preset previews and the composite grid exist."""
    PREVIEWS_DIR.mkdir(parents=True, exist_ok=True)

    if force and PREVIEW_GRID_PATH.exists():
        PREVIEW_GRID_PATH.unlink()

    preview_paths: list[Path] = []
    for preset in PRESETS:
        out = PREVIEWS_DIR / f"{preset.key}.png"
        if force and out.exists():
            out.unlink()
        try:
            path = await _render_single(preset)
            preview_paths.append(path)
        except Exception as exc:
            logger.exception("preview render failed for %s: %s", preset.key, exc)
            # Fall back to a blank cell so the grid still renders.
            fallback = PREVIEWS_DIR / f"{preset.key}.png"
            Image.new("RGB", (PREVIEW_W, PREVIEW_H), (30, 30, 40)).save(fallback)
            preview_paths.append(fallback)

    if not PREVIEW_GRID_PATH.exists():
        _compose_grid(preview_paths, [p.title for p in PRESETS], PREVIEW_GRID_PATH)
    return PREVIEW_GRID_PATH


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(ensure_previews(force=True))
    print(f"Grid written to {PREVIEW_GRID_PATH}")
