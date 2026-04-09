"""Python wrapper around ``npx remotion render``.

Renders a Remotion composition by shelling out to the node-based CLI
installed in the ``remotion/`` subproject. Props are written to a temp
JSON file and passed via ``--props``; this avoids shell-escaping issues
with large caption arrays.
"""
import asyncio
import json
from pathlib import Path

from config import REMOTION_ROOT


class RemotionError(RuntimeError):
    pass


async def _run(*args: str, cwd: Path) -> None:
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(cwd),
    )
    out, err = await proc.communicate()
    if proc.returncode != 0:
        tail = (err.decode(errors="ignore") + out.decode(errors="ignore"))[-4000:]
        raise RemotionError(
            f"{' '.join(args)} failed (rc={proc.returncode}):\n{tail}"
        )


async def render_captioned_video(
    *,
    video_path: Path,
    captions: list[dict],
    preset_key: str,
    duration_seconds: float,
    output_path: Path,
    fps: int = 30,
    concurrency: int = 1,
) -> None:
    """Render the ``CaptionedVideo`` composition to ``output_path``.

    Parameters
    ----------
    video_path:
        Absolute path to the user's uploaded video. Remotion can read a
        local file via ``file://`` URL.
    captions:
        Remotion-compatible ``Caption[]`` (see ``transcribe.py``).
    preset_key:
        One of ``hormozi``, ``beast``, ``neon``, ``minimal``.
    duration_seconds:
        Duration of the rendered composition in seconds. Usually equal
        to the source video duration.
    output_path:
        Where to write the rendered mp4.
    """
    if not REMOTION_ROOT.exists():
        raise RemotionError(f"Remotion project not found: {REMOTION_ROOT}")

    video_path = video_path.resolve()
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    props = {
        "videoSrc": f"file://{video_path}",
        "captions": captions,
        "presetKey": preset_key,
        "durationInSeconds": float(duration_seconds),
        "fps": fps,
    }

    props_path = output_path.with_suffix(".props.json")
    props_path.write_text(json.dumps(props), encoding="utf-8")

    try:
        # Entry point is configured in remotion.config.ts via
        # Config.setEntryPoint("src/index.ts"), so we don't pass it here.
        await _run(
            "npx",
            "--yes",
            "remotion",
            "render",
            "CaptionedVideo",
            str(output_path),
            f"--props={props_path}",
            f"--concurrency={concurrency}",
            "--codec=h264",
            "--log=error",
            cwd=REMOTION_ROOT,
        )
    finally:
        try:
            props_path.unlink()
        except FileNotFoundError:
            pass
