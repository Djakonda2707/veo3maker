"""ffmpeg / ffprobe helpers used by the Remotion pipeline."""
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


async def probe_duration(video_path: Path) -> float:
    """Return the container duration of ``video_path`` in seconds."""
    proc = await asyncio.create_subprocess_exec(
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(video_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await proc.communicate()
    if proc.returncode != 0:
        raise FFmpegError(err.decode(errors="ignore"))
    raw = out.decode().strip()
    if not raw:
        raise FFmpegError(f"Empty ffprobe duration output for {video_path}")
    return float(raw)
