"""Per-segment production helpers tying the providers to a Run.

Each 10s segment goes: first frame (with the fixed character ref) → animate.
Claude Code drives the QC between these steps by reading the generated PNG
and deciding whether to regenerate before animating.
"""
from __future__ import annotations

import logging
from pathlib import Path

from . import pconfig
from .providers import images, video
from .run import Run

logger = logging.getLogger("pipeline.production")


async def make_first_frame(run: Run, index: int) -> Path:
    seg = run.segments[index]
    prompt = seg.first_frame_prompt or seg.prompt
    if not prompt:
        raise ValueError(f"segment {index} has no prompt yet")
    out = run.frame_path(index)
    path = await images.generate_first_frame(prompt, run.character_ref, out)
    seg.first_frame_path = str(path)
    run.save()
    return path


async def animate_segment(run: Run, index: int) -> Path:
    seg = run.segments[index]
    frame = run.frame_path(index)
    if not frame.exists():
        raise FileNotFoundError(
            f"first frame for segment {index} missing — generate it first"
        )
    motion = seg.motion_prompt or seg.prompt
    out = run.clip_path(index)
    path = await video.animate(frame, motion, out, seconds=pconfig.SEGMENT_SECONDS)
    seg.clip_path = str(path)
    run.save()
    return path


async def produce_segment(run: Run, index: int) -> Path:
    await make_first_frame(run, index)
    return await animate_segment(run, index)


async def produce_all(run: Run) -> list[Path]:
    """First-frame + animate every segment that has a prompt.

    Used by the one-shot ``produce`` command. For real (non-mock) runs you
    usually want Claude to QC frames between steps instead.
    """
    clips: list[Path] = []
    for seg in run.segments:
        if not (seg.prompt or seg.first_frame_prompt):
            logger.warning("segment %d has no prompt — skipping", seg.index)
            continue
        clips.append(await produce_segment(run, seg.index))
    return clips
