"""Build an ASS subtitle file with animated per-word highlighting.

The effect: a short phrase (a few words) is shown on screen; the currently
spoken word is shown larger and in a highlight color with a quick pop-in
animation.  This mimics the popular TikTok / Reels caption style.
"""
from typing import Iterable


ASS_HEADER_TEMPLATE = """[Script Info]
ScriptType: v4.00+
PlayResX: {play_res_x}
PlayResY: {play_res_y}
WrapStyle: 2
ScaledBorderAndShadow: yes
Collisions: Normal

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,{outline},{shadow},{alignment},60,60,{marginv},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _fmt_time(t: float) -> str:
    """Format seconds as H:MM:SS.cc for ASS."""
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
    max_duration: float,
    max_gap: float,
) -> list[list[dict]]:
    phrases: list[list[dict]] = []
    current: list[dict] = []
    for w in words:
        if not current:
            current.append(w)
            continue
        prev = current[-1]
        gap = w["start"] - prev["end"]
        phrase_duration = w["end"] - current[0]["start"]
        if (
            len(current) >= max_words
            or phrase_duration > max_duration
            or gap > max_gap
        ):
            phrases.append(current)
            current = [w]
        else:
            current.append(w)
    if current:
        phrases.append(current)
    return phrases


def build_ass(
    words: Iterable[dict],
    play_res_x: int = 1920,
    play_res_y: int = 1080,
    font: str = "Arial",
    font_size: int = 80,
    max_words_per_phrase: int = 3,
    max_phrase_duration: float = 2.5,
    max_word_gap: float = 0.8,
    position: str = "bottom",
    highlight_color: str = "&H0000FFFF&",  # yellow in ASS BBGGRR
) -> str:
    """Generate the full ASS file content as a string."""
    words = list(words)
    if not words:
        return ""

    alignment_map = {"bottom": 2, "middle": 5, "top": 8}
    alignment = alignment_map.get(position, 2)
    marginv = int(play_res_y * 0.12) if position != "middle" else 0
    outline = max(2, int(font_size * 0.06))
    shadow = max(1, int(font_size * 0.03))

    header = ASS_HEADER_TEMPLATE.format(
        play_res_x=play_res_x,
        play_res_y=play_res_y,
        font=font,
        size=font_size,
        outline=outline,
        shadow=shadow,
        alignment=alignment,
        marginv=marginv,
    )

    phrases = _group_phrases(
        words,
        max_words=max_words_per_phrase,
        max_duration=max_phrase_duration,
        max_gap=max_word_gap,
    )

    lines: list[str] = []
    for phrase in phrases:
        phrase_start = phrase[0]["start"]
        phrase_end = phrase[-1]["end"]

        for i, word in enumerate(phrase):
            active_start = word["start"] if i > 0 else phrase_start
            if i + 1 < len(phrase):
                active_end = phrase[i + 1]["start"]
            else:
                active_end = phrase_end
            if active_end <= active_start:
                continue

            parts: list[str] = []
            for j, w in enumerate(phrase):
                text = _escape(w["text"])
                if j == i:
                    # Pop animation: 115% -> 130% -> 115%, yellow color.
                    parts.append(
                        f"{{\\c{highlight_color}\\fscx115\\fscy115"
                        f"\\t(0,120,\\fscx130\\fscy130)"
                        f"\\t(120,240,\\fscx115\\fscy115)}}"
                        f"{text}{{\\r}}"
                    )
                else:
                    parts.append(text)
            line_text = " ".join(parts)

            lines.append(
                f"Dialogue: 0,{_fmt_time(active_start)},"
                f"{_fmt_time(active_end)},Default,,0,0,0,,{line_text}"
            )

    return header + "\n".join(lines) + "\n"
