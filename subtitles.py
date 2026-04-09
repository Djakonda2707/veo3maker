"""Build ASS subtitle files for a given Preset.

The shape of the output depends on the preset:
* ``highlight_effect='none'`` — one static phrase per Dialogue line.
* otherwise — one Dialogue per active word, the active word is wrapped
  with override tags (scale pop / alpha+blur glow / plain color swap).

``layout='horizontal'`` joins words with spaces, ``layout='stack'`` joins
them with ``\\N`` so libass draws them on separate lines.
"""
from typing import Iterable

from presets import Preset


ASS_HEADER_TEMPLATE = """[Script Info]
ScriptType: v4.00+
PlayResX: {play_res_x}
PlayResY: {play_res_y}
WrapStyle: 0
ScaledBorderAndShadow: yes
Collisions: Normal

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{size},{primary},&H00FFFFFF,{outline_color},&H64000000,{bold},{italic},0,0,100,100,0,0,1,{outline},{shadow},{alignment},60,60,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _fmt_time(t: float) -> str:
    if t < 0:
        t = 0.0
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t - h * 3600 - m * 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace("{", "\\{")
        .replace("}", "\\}")
        .replace("\n", "\\N")
    )


def _group_phrases(
    words: list[dict],
    max_words: int,
    max_duration: float = 2.5,
    max_gap: float = 0.8,
) -> list[list[dict]]:
    phrases: list[list[dict]] = []
    current: list[dict] = []
    for w in words:
        if not current:
            current.append(w)
            continue
        prev = current[-1]
        gap = w["start"] - prev["end"]
        duration = w["end"] - current[0]["start"]
        if (
            len(current) >= max_words
            or duration > max_duration
            or gap > max_gap
        ):
            phrases.append(current)
            current = [w]
        else:
            current.append(w)
    if current:
        phrases.append(current)
    return phrases


def _highlight_wrap(text: str, preset: Preset) -> str:
    """Return ``text`` wrapped with ASS override tags for its highlight."""
    effect = preset.highlight_effect
    color = preset.highlight_color

    if effect == "pop":
        return (
            f"{{\\c{color}\\fscx60\\fscy60"
            f"\\t(0,90,\\fscx130\\fscy130)"
            f"\\t(90,200,\\fscx115\\fscy115)}}"
            f"{text}{{\\r}}"
        )
    if effect == "glow":
        return (
            f"{{\\c{color}\\blur6\\alpha&H80&"
            f"\\t(0,220,\\blur0\\alpha&H00&)}}"
            f"{text}{{\\r}}"
        )
    if effect == "color":
        return f"{{\\c{color}}}{text}{{\\r}}"
    # "none" — no wrapping
    return text


def _build_header(
    play_res_x: int,
    play_res_y: int,
    preset: Preset,
) -> str:
    font_size = max(24, int(play_res_y * preset.font_size_ratio))
    outline = max(2, int(font_size * preset.outline_ratio))
    shadow = max(0, int(font_size * preset.shadow_ratio))

    alignment = {"top": 8, "middle": 5, "bottom": 2}.get(preset.position, 2)
    if preset.position == "middle":
        margin_v = 0
    else:
        margin_v = int(play_res_y * preset.margin_v_ratio)

    return ASS_HEADER_TEMPLATE.format(
        play_res_x=play_res_x,
        play_res_y=play_res_y,
        font=preset.font,
        size=font_size,
        primary=preset.base_color,
        outline_color=preset.outline_color,
        bold=-1 if preset.bold else 0,
        italic=-1 if preset.italic else 0,
        outline=outline,
        shadow=shadow,
        alignment=alignment,
        margin_v=margin_v,
    )


def _build_phrase_events(phrase: list[dict], preset: Preset) -> list[str]:
    phrase_start = phrase[0]["start"]
    phrase_end = phrase[-1]["end"] + 0.1
    separator = " " if preset.layout == "horizontal" else "\\N"

    # No per-word highlight — show the whole phrase as one line.
    if preset.highlight_effect == "none":
        text = separator.join(_escape(w["text"]) for w in phrase)
        return [
            f"Dialogue: 0,{_fmt_time(phrase_start)},"
            f"{_fmt_time(phrase_end)},Default,,0,0,0,,{text}"
        ]

    events: list[str] = []
    for i, word in enumerate(phrase):
        active_start = word["start"] if i > 0 else phrase_start
        active_end = phrase[i + 1]["start"] if i + 1 < len(phrase) else phrase_end
        if active_end <= active_start:
            continue

        parts: list[str] = []
        for j, w in enumerate(phrase):
            escaped = _escape(w["text"])
            parts.append(_highlight_wrap(escaped, preset) if j == i else escaped)
        line_text = separator.join(parts)

        events.append(
            f"Dialogue: 0,{_fmt_time(active_start)},"
            f"{_fmt_time(active_end)},Default,,0,0,0,,{line_text}"
        )
    return events


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def build_ass(
    words: Iterable[dict],
    play_res_x: int,
    play_res_y: int,
    preset: Preset,
) -> str:
    words = list(words)
    if not words:
        return ""

    if preset.uppercase:
        words = [{**w, "text": w["text"].upper()} for w in words]

    phrases = _group_phrases(words, max_words=preset.max_words_per_phrase)

    header = _build_header(play_res_x, play_res_y, preset)
    events: list[str] = []
    for phrase in phrases:
        events.extend(_build_phrase_events(phrase, preset))

    return header + "\n".join(events) + "\n"
