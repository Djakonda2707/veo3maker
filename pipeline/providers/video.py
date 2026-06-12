"""Animate a first frame into a clip (image -> video).

Backends (``pconfig.VIDEO_PROVIDER``):

* ``mock`` — Ken-Burns zoom over the still via ffmpeg. Real mp4, zero spend.
* ``fal``  — fal.ai image-to-video (Wan 2.5 default; Kling/Seedance by
             swapping ``FAL_VIDEO_MODEL``). Pay-per-use, no subscription.
"""
from __future__ import annotations

import base64
import logging
from pathlib import Path

from .. import pconfig
from .base import ProviderError, download, make_placeholder_clip, poll_until

logger = logging.getLogger("pipeline.video")


def _mock_animate(image_path: Path, prompt: str, seconds: float, out: Path) -> Path:
    return make_placeholder_clip(
        image_path, out, seconds, pconfig.FPS,
        pconfig.VIDEO_WIDTH, pconfig.VIDEO_HEIGHT,
    )


async def _fal_animate(image_path: Path, prompt: str, seconds: float, out: Path) -> Path:
    """Submit an image-to-video job to fal.ai and download the result.

    fal's queue API: POST to the model URL returns either a finished payload
    or a status/response url to poll. Image is sent as a base64 data URI.
    """
    import httpx

    if not pconfig.FAL_API_KEY:
        raise ProviderError("FAL_API_KEY is not set (provider=fal)")

    b64 = base64.b64encode(image_path.read_bytes()).decode()
    submit_url = f"https://queue.fal.run/{pconfig.FAL_VIDEO_MODEL}"
    headers = {"Authorization": f"Key {pconfig.FAL_API_KEY}"}
    payload = {
        "image_url": f"data:image/png;base64,{b64}",
        "prompt": prompt,
        "duration": int(round(seconds)),
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(submit_url, headers=headers, json=payload)
        if resp.status_code >= 400:
            raise ProviderError(f"fal submit {resp.status_code}: {resp.text[:400]}")
        job = resp.json()

    status_url = job.get("status_url")
    response_url = job.get("response_url")

    async def _check():
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.get(status_url, headers=headers)
            st = r.json()
            if st.get("status") == "COMPLETED":
                rr = await client.get(response_url, headers=headers)
                return rr.json()
            if st.get("status") in {"FAILED", "ERROR"}:
                raise ProviderError(f"fal job failed: {str(st)[:300]}")
            return None

    result = job if "video" in job else await poll_until(_check, interval=5.0, max_wait=900.0)
    video_url = (result.get("video") or {}).get("url") if isinstance(result, dict) else None
    if not video_url:
        raise ProviderError(f"no video url in fal result: {str(result)[:400]}")
    return await download(video_url, out)


async def animate(
    image_path: str | Path,
    prompt: str,
    out_path: str | Path,
    seconds: float | None = None,
) -> Path:
    img = Path(image_path)
    out = Path(out_path)
    secs = seconds if seconds is not None else pconfig.SEGMENT_SECONDS
    provider = "mock" if pconfig.DRY_RUN else pconfig.VIDEO_PROVIDER

    if provider == "mock":
        logger.info("animate[mock] %s -> %s (%.0fs)", img.name, out.name, secs)
        return _mock_animate(img, prompt, secs, out)
    if provider == "fal":
        logger.info("animate[fal:%s] %s -> %s", pconfig.FAL_VIDEO_MODEL, img.name, out.name)
        return await _fal_animate(img, prompt, secs, out)
    raise ProviderError(f"unknown VIDEO_PROVIDER: {provider}")
