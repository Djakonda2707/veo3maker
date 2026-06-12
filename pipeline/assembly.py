"""Assemble per-segment clips into the final reel (ffmpeg) and, optionally,
burn animated subtitles via the existing Remotion renderer.

Kept independent of the Telegram bot's ``config.py`` (which hard-requires a
BOT_TOKEN) so the pipeline CLI runs without a bot token.
"""
from __future__ import annotations

import asyncio
import json
import logging
import subprocess
from pathlib import Path

from . import pconfig
from .run import Run

logger = logging.getLogger("pipeline.assembly")


class AssemblyError(RuntimeError):
    pass


def _ffmpeg(*args: str) -> None:
    cmd = ["ffmpeg", "-y", "-loglevel", "error", *args]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise AssemblyError(f"ffmpeg failed:\n{proc.stderr[-2000:]}")


def concat_clips(run: Run, music: str | Path | None = None) -> Path:
    """Concatenate all segment clips in order into ``raw.mp4``.

    Clips already share resolution/fps (produced by the animate stage), so
    we use the fast concat demuxer. Optional background music is mixed in as
    the audio track.
    """
    clips = [run.clip_path(s.index) for s in run.segments]
    missing = [c.name for c in clips if not c.exists()]
    if missing:
        raise AssemblyError(f"missing clips, animate them first: {missing}")

    list_file = run.dir / "concat.txt"
    list_file.write_text(
        "".join(f"file '{c.resolve()}'\n" for c in clips), encoding="utf-8"
    )

    out = run.raw_path
    music_path = Path(music) if music else None
    if music_path and music_path.exists():
        _ffmpeg(
            "-f", "concat", "-safe", "0", "-i", str(list_file),
            "-i", str(music_path),
            "-map", "0:v:0", "-map", "1:a:0", "-shortest",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", str(out),
        )
    else:
        _ffmpeg(
            "-f", "concat", "-safe", "0", "-i", str(list_file),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out),
        )
    list_file.unlink(missing_ok=True)
    logger.info("assembled %d clips -> %s", len(clips), out.name)
    return out


def probe_duration(path: Path) -> float:
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True,
    )
    try:
        return float(proc.stdout.strip())
    except ValueError:
        return 0.0


async def burn_subtitles(
    run: Run, voiceover: str | Path, preset: str | None = None
) -> Path:
    """Transcribe a voiceover track and burn animated captions onto raw.mp4.

    Reuses ``transcribe.py`` (standalone) and shells out to Remotion using
    ``pconfig.REMOTION_ROOT`` — no dependency on the bot's config.
    """
    from transcribe import transcribe_audio  # repo root on sys.path

    if not run.raw_path.exists():
        raise AssemblyError("raw.mp4 missing — run `assemble` first")
    vo = Path(voiceover)
    if not vo.exists():
        raise AssemblyError(f"voiceover not found: {vo}")

    # Extract a wav for whisper.
    wav = run.dir / "voiceover.wav"
    _ffmpeg("-i", str(vo), "-ac", "1", "-ar", "16000", str(wav))
    captions, _lang = await asyncio.to_thread(
        transcribe_audio, str(wav), "small", "cpu", "int8", None
    )
    if not captions:
        raise AssemblyError("no speech recognised in voiceover")

    duration = probe_duration(run.raw_path)
    props = {
        "videoSrc": f"file://{run.raw_path.resolve()}",
        "captions": captions,
        "presetKey": preset or pconfig.SUBTITLE_PRESET,
        "durationInSeconds": duration,
        "fps": pconfig.FPS,
    }
    props_path = run.dir / "subs.props.json"
    props_path.write_text(json.dumps(props), encoding="utf-8")

    proc = await asyncio.create_subprocess_exec(
        "npx", "--yes", "remotion", "render", "CaptionedVideo",
        str(run.final_path), f"--props={props_path}",
        "--codec=h264", "--log=error",
        cwd=str(pconfig.REMOTION_ROOT),
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    out, err = await proc.communicate()
    props_path.unlink(missing_ok=True)
    if proc.returncode != 0:
        tail = (err.decode(errors="ignore") + out.decode(errors="ignore"))[-3000:]
        raise AssemblyError(f"remotion render failed:\n{tail}")
    logger.info("burned subtitles -> %s", run.final_path.name)
    return run.final_path
