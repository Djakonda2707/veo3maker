"""ffmpeg / ffprobe helpers."""
import asyncio
from pathlib import Path


class FFmpegError(RuntimeError):
    pass


async def _run(*args: str, cwd: str | None = None) -> None:
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
    )
    _, err = await proc.communicate()
    if proc.returncode != 0:
        tail = err.decode(errors="ignore")[-2000:]
        raise FFmpegError(f"{args[0]} failed (rc={proc.returncode}):\n{tail}")


def _subtitles_filter(ass_name: str, fonts_dir: Path | None) -> str:
    """Build the ffmpeg ``subtitles=`` filter arg, optionally with fontsdir."""
    parts = [f"subtitles={ass_name}"]
    if fonts_dir and fonts_dir.exists():
        # Absolute path with no ':' or ',' is safe to pass as-is.
        parts.append(f"fontsdir={fonts_dir.resolve()}")
    return ":".join(parts)


async def extract_audio(input_path: Path, output_path: Path) -> None:
    """Extract mono 16 kHz WAV suitable for Whisper."""
    await _run(
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        str(output_path),
    )


async def probe_size(video_path: Path) -> tuple[int, int]:
    proc = await asyncio.create_subprocess_exec(
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "csv=p=0",
        str(video_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await proc.communicate()
    if proc.returncode != 0:
        raise FFmpegError(err.decode(errors="ignore"))
    parts = out.decode().strip().split(",")
    if len(parts) < 2:
        raise FFmpegError(f"Unexpected ffprobe output: {out!r}")
    return int(parts[0]), int(parts[1])


async def burn_subtitles(
    input_path: Path,
    subs_path: Path,
    output_path: Path,
    fonts_dir: Path | None = None,
) -> None:
    """Burn ASS subtitles into a video file via libass.

    We set ``cwd`` to the subtitles directory and reference the .ass file by
    basename to side-step the escaping rules of the ``subtitles`` filter.
    """
    cwd = str(subs_path.parent)
    vf = _subtitles_filter(subs_path.name, fonts_dir)
    await _run(
        "ffmpeg",
        "-y",
        "-i",
        str(input_path.resolve()),
        "-vf",
        vf,
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-movflags",
        "+faststart",
        str(output_path.resolve()),
        cwd=cwd,
    )


async def render_subtitle_frame(
    subs_path: Path,
    output_path: Path,
    width: int = 1080,
    height: int = 1920,
    bg_color: str = "0x1a1a2e",
    ts: float = 0.4,
    fonts_dir: Path | None = None,
) -> None:
    """Render a single frame of a solid-colour background with the subtitles
    applied, captured at time ``ts``. Used for preset previews.
    """
    cwd = str(subs_path.parent)
    vf = _subtitles_filter(subs_path.name, fonts_dir)
    await _run(
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c={bg_color}:s={width}x{height}:d=3",
        "-vf",
        vf,
        "-ss",
        f"{ts:.2f}",
        "-frames:v",
        "1",
        str(output_path.resolve()),
        cwd=cwd,
    )
