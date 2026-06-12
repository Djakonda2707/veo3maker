"""First-frame generation (Nano Banana / Gemini image).

The guide's key trick for keeping the AI creator identical across every
reel is to feed a *fixed character photo* as a reference into each first
frame. So every backend here takes ``character_ref`` (a path) plus a text
prompt and returns a generated PNG.

Backends (``pconfig.IMAGE_PROVIDER``):

* ``mock``   — composite the character photo into a 9:16 frame with the
               prompt overlaid. Real file, zero spend, always works.
* ``relay``  — OpenAI/Gemini-compatible HTTP endpoint (laozhang.ai by
               default, or Google's OpenAI-compat base). Best-effort; the
               request shape is documented inline and easy to tweak.
"""
from __future__ import annotations

import base64
import logging
from pathlib import Path

from .. import pconfig
from .base import ProviderError, make_placeholder_image

logger = logging.getLogger("pipeline.images")


def _mock_first_frame(prompt: str, character_ref: Path | None, out: Path) -> Path:
    from PIL import Image, ImageDraw, ImageFont

    W, H = pconfig.VIDEO_WIDTH, pconfig.VIDEO_HEIGHT
    out.parent.mkdir(parents=True, exist_ok=True)

    if character_ref and Path(character_ref).exists():
        base = Image.open(character_ref).convert("RGB")
        # Cover-fit the character photo into 9:16.
        scale = max(W / base.width, H / base.height)
        base = base.resize((int(base.width * scale), int(base.height * scale)))
        left = (base.width - W) // 2
        top = (base.height - H) // 2
        frame = base.crop((left, top, left + W, top + H))
        # Dim the lower third so overlay text stays readable.
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.rectangle([0, int(H * 0.7), W, H], fill=(0, 0, 0, 140))
        frame = Image.alpha_composite(frame.convert("RGBA"), overlay).convert("RGB")
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", size=max(30, W // 20))
        except OSError:
            font = ImageFont.load_default()
        draw = ImageDraw.Draw(frame)
        text = (prompt[:60] + "…") if len(prompt) > 60 else prompt
        draw.text((40, int(H * 0.74)), text, fill=(255, 255, 255), font=font)
        frame.save(out, "PNG")
        return out

    # No character photo: fall back to a plain captioned placeholder.
    return make_placeholder_image(prompt, out, W, H, seed=str(character_ref))


async def _relay_first_frame(prompt: str, character_ref: Path | None, out: Path) -> Path:
    """OpenAI/Gemini-compatible image call (laozhang.ai / Google OpenAI-compat).

    Uses the chat/completions multimodal shape so a reference photo can be
    passed alongside the prompt — that's what keeps the character consistent.
    The model is expected to return an image (inline base64 data URL). If a
    relay only supports ``images/generations`` (text-only), set a prompt that
    describes the character instead of relying on the reference.
    """
    import httpx

    if not pconfig.IMAGE_API_KEY:
        raise ProviderError("IMAGE_API_KEY is not set (provider=relay)")

    content: list[dict] = [{"type": "text", "text": prompt}]
    if character_ref and Path(character_ref).exists():
        b64 = base64.b64encode(Path(character_ref).read_bytes()).decode()
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
            }
        )

    url = pconfig.IMAGE_API_BASE_URL.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {pconfig.IMAGE_API_KEY}"}
    payload = {
        "model": pconfig.IMAGE_MODEL,
        "messages": [{"role": "user", "content": content}],
        "modalities": ["image", "text"],
    }

    async with httpx.AsyncClient(timeout=180.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        if resp.status_code >= 400:
            raise ProviderError(
                f"relay image {resp.status_code}: {resp.text[:400]}"
            )
        data = resp.json()

    img_b64 = _extract_image_b64(data)
    if not img_b64:
        raise ProviderError(f"no image in relay response: {str(data)[:400]}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(base64.b64decode(img_b64))
    return out


def _extract_image_b64(data: dict) -> str | None:
    """Pull a base64 image out of the various shapes relays return."""
    # OpenAI images/generations style
    for item in (data.get("data") or []):
        if item.get("b64_json"):
            return item["b64_json"]
    # chat/completions multimodal style
    for choice in (data.get("choices") or []):
        msg = choice.get("message", {})
        for img in (msg.get("images") or []):
            url = (img.get("image_url") or {}).get("url", "")
            if url.startswith("data:") and "base64," in url:
                return url.split("base64,", 1)[1]
        content = msg.get("content")
        if isinstance(content, str) and "base64," in content:
            return content.split("base64,", 1)[1].strip()
    return None


async def generate_first_frame(
    prompt: str, character_ref: str | Path | None, out_path: str | Path
) -> Path:
    out = Path(out_path)
    ref = Path(character_ref) if character_ref else None
    provider = "mock" if pconfig.DRY_RUN else pconfig.IMAGE_PROVIDER

    if provider == "mock":
        logger.info("first_frame[mock] -> %s", out.name)
        return _mock_first_frame(prompt, ref, out)
    if provider == "relay":
        logger.info("first_frame[relay:%s] -> %s", pconfig.IMAGE_MODEL, out.name)
        return await _relay_first_frame(prompt, ref, out)
    raise ProviderError(f"unknown IMAGE_PROVIDER: {provider}")
