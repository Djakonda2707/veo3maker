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


async def extract_audio(input_path: Path, output_path: Path) -> None:
    """Extract mono 16kHz WAV suitable for Whisper."""
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
) -> None:
    """Burn ASS subtitles into the video.

    We run ffmpeg with cwd set to the subtitles' directory so that we can
    reference the .ass file by its plain basename and avoid the notorious
    escaping rules of the ``subtitles`` filter (colons, commas, backslashes).
    """
    cwd = str(subs_path.parent)
    await _run(
        "ffmpeg",
        "-y",
        "-i",
        str(input_path.resolve()),
        "-vf",
        f"subtitles={subs_path.name}",
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
