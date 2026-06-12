"""Shared helpers for providers: HTTP, retries, and offline mock artifacts.

The mock artifact builders are real: they write actual PNG/MP4 files
(via Pillow + ffmpeg) so downstream stages — assembly, subtitles — have
something concrete to operate on even with zero API spend.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger("pipeline.providers")


class ProviderError(RuntimeError):
    pass


def _color_from(seed: str) -> tuple[int, int, int]:
    h = hashlib.sha256(seed.encode("utf-8")).digest()
    # Keep it darkish so white overlay text stays readable.
    return (40 + h[0] % 120, 40 + h[1] % 120, 40 + h[2] % 120)


def make_placeholder_image(
    text: str, out_path: Path, width: int, height: int, seed: str = ""
) -> Path:
    """Write a vertical placeholder 'first frame' with wrapped caption text."""
    from PIL import Image, ImageDraw, ImageFont

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (width, height), _color_from(seed or text))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", size=max(28, width // 22))
    except OSError:
        font = ImageFont.load_default()

    # Naive word wrap to ~22 chars per line.
    words, lines, line = text.split(), [], ""
    for w in words:
        if len(line) + len(w) + 1 > 22:
            lines.append(line)
            line = w
        else:
            line = f"{line} {w}".strip()
    if line:
        lines.append(line)
    lines = lines[:8] or ["(frame)"]

    line_h = max(34, height // 28)
    total = line_h * len(lines)
    y = (height - total) // 2
    for ln in lines:
        bbox = draw.textbbox((0, 0), ln, font=font)
        x = (width - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), ln, fill=(245, 245, 245), font=font)
        y += line_h

    img.save(out_path, "PNG")
    return out_path


def _has_ffmpeg() -> bool:
    from shutil import which

    return which("ffmpeg") is not None


def make_placeholder_clip(
    image_path: Path,
    out_path: Path,
    seconds: float,
    fps: int,
    width: int,
    height: int,
) -> Path:
    """Animate a still into a short clip with a slow zoom (Ken Burns).

    Falls back to copying the still as a 1-frame-ish video-less artifact if
    ffmpeg is unavailable, so the pipeline still produces *a* file.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not _has_ffmpeg():
        logger.warning("ffmpeg not found; writing still copy as clip artifact")
        out_path.write_bytes(image_path.read_bytes())
        return out_path

    frames = max(1, int(round(seconds * fps)))
    vf = (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},"
        f"zoompan=z='min(zoom+0.0008,1.12)':d={frames}:"
        f"s={width}x{height}:fps={fps}"
    )
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-loop", "1", "-i", str(image_path),
        "-t", f"{seconds}",
        "-vf", vf,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(fps),
        str(out_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise ProviderError(f"ffmpeg clip failed:\n{proc.stderr[-2000:]}")
    return out_path


async def post_json(
    url: str, headers: dict, payload: dict, timeout: float = 120.0
) -> dict:
    import httpx

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, headers=headers, json=payload)
        if resp.status_code >= 400:
            raise ProviderError(f"POST {url} -> {resp.status_code}: {resp.text[:500]}")
        return resp.json()


async def get_json(url: str, headers: dict, params: dict | None = None,
                   timeout: float = 60.0) -> dict:
    import httpx

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get(url, headers=headers, params=params or {})
        if resp.status_code >= 400:
            raise ProviderError(f"GET {url} -> {resp.status_code}: {resp.text[:500]}")
        return resp.json()


async def download(url: str, out_path: Path, timeout: float = 300.0) -> Path:
    import httpx

    out_path.parent.mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        out_path.write_bytes(resp.content)
    return out_path


async def poll_until(
    check, *, interval: float = 5.0, max_wait: float = 600.0
):
    """Await ``check()`` (async, returns result-or-None) until non-None."""
    waited = 0.0
    while waited < max_wait:
        result = await check()
        if result is not None:
            return result
        await asyncio.sleep(interval)
        waited += interval
    raise ProviderError(f"polling timed out after {max_wait}s")
