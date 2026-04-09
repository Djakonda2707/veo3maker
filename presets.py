"""Subtitle style presets shown in the bot menu.

Each preset is a frozen dataclass with enough information to both render the
final subtitles and produce a preview image for the picker.

ASS colours are in ``&HAABBGGRR&`` format (alpha / blue / green / red).
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Preset:
    key: str
    title: str
    sample_text: str

    font: str
    font_size_ratio: float  # fraction of video height
    max_words_per_phrase: int
    position: str           # top / middle / bottom
    layout: str             # horizontal / stack
    margin_v_ratio: float = 0.12

    base_color: str = "&H00FFFFFF&"       # white
    highlight_color: str = "&H0000FFFF&"  # yellow
    outline_color: str = "&H00000000&"    # black
    outline_ratio: float = 0.06
    shadow_ratio: float = 0.02

    bold: bool = True
    italic: bool = False
    uppercase: bool = False

    highlight_effect: str = "pop"  # pop / glow / color / none


PRESETS: list[Preset] = [
    # 1 ─ Minimal: clean white sans, whole phrase at once, bottom.
    Preset(
        key="minimal",
        title="1. Minimal",
        sample_text="clean minimal style",
        font="Inter",
        font_size_ratio=0.055,
        max_words_per_phrase=5,
        position="bottom",
        layout="horizontal",
        margin_v_ratio=0.08,
        base_color="&H00FFFFFF&",
        highlight_color="&H00FFFFFF&",
        outline_color="&HA0000000&",
        outline_ratio=0.04,
        shadow_ratio=0.03,
        bold=True,
        highlight_effect="none",
    ),
    # 2 ─ Bold Stack: heavy sans, 1-2 words stacked, light-blue highlight.
    Preset(
        key="bold_stack",
        title="2. Bold Stack",
        sample_text="bold stack",
        font="Inter",
        font_size_ratio=0.095,
        max_words_per_phrase=2,
        position="middle",
        layout="stack",
        margin_v_ratio=0.0,
        base_color="&H00FFFFFF&",
        highlight_color="&H00FFCC66&",  # RGB 66CCFF light blue
        outline_color="&H00000000&",
        outline_ratio=0.09,
        shadow_ratio=0.03,
        bold=True,
        highlight_effect="pop",
    ),
    # 3 ─ Caps Pop: UPPERCASE condensed heavy sans, orange highlight.
    Preset(
        key="caps_pop",
        title="3. Caps Pop",
        sample_text="caps pop style",
        font="Anton",
        font_size_ratio=0.11,
        max_words_per_phrase=3,
        position="middle",
        layout="stack",
        margin_v_ratio=0.0,
        base_color="&H00FFFFFF&",
        highlight_color="&H000099FF&",  # RGB FF9900 orange
        outline_color="&H00000000&",
        outline_ratio=0.08,
        shadow_ratio=0.02,
        uppercase=True,
        bold=True,
        highlight_effect="pop",
    ),
    # 4 ─ Neon Glow: electric-lime letters with heavy glow, stacked.
    Preset(
        key="neon_glow",
        title="4. Neon Glow",
        sample_text="neon glow style",
        font="Inter",
        font_size_ratio=0.095,
        max_words_per_phrase=3,
        position="middle",
        layout="stack",
        margin_v_ratio=0.0,
        base_color="&H0000FFD4&",       # RGB D4FF00 electric lime
        highlight_color="&H0000FFFF&",  # brighter yellow-green
        outline_color="&H0000AA33&",    # dark green outline
        outline_ratio=0.13,
        shadow_ratio=0.0,
        uppercase=True,
        bold=True,
        highlight_effect="glow",
    ),
    # 5 ─ Big Yellow: one massive word at a time, yellow caps, top of frame.
    Preset(
        key="big_yellow",
        title="5. Big Yellow",
        sample_text="yellow",
        font="Bebas Neue",
        font_size_ratio=0.16,
        max_words_per_phrase=1,
        position="top",
        layout="stack",
        margin_v_ratio=0.14,
        base_color="&H0000FFFF&",       # yellow
        highlight_color="&H0000FFFF&",
        outline_color="&H00000000&",
        outline_ratio=0.06,
        shadow_ratio=0.04,
        uppercase=True,
        bold=True,
        highlight_effect="pop",
    ),
    # 6 ─ Red Serif: one dramatic serif word, italic red, top of frame.
    Preset(
        key="red_serif",
        title="6. Red Serif",
        sample_text="serif",
        font="Playfair Display",
        font_size_ratio=0.17,
        max_words_per_phrase=1,
        position="top",
        layout="stack",
        margin_v_ratio=0.14,
        base_color="&H003B33EF&",       # RGB EF333B red
        highlight_color="&H003B33EF&",
        outline_color="&H00000000&",
        outline_ratio=0.04,
        shadow_ratio=0.03,
        uppercase=True,
        bold=True,
        italic=True,
        highlight_effect="pop",
    ),
]

PRESET_BY_KEY: dict[str, Preset] = {p.key: p for p in PRESETS}
DEFAULT_PRESET_KEY = "caps_pop"
