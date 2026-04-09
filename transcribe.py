"""Speech-to-text with word-level timestamps via faster-whisper.

Returns Remotion-compatible Caption[] objects, matching the
``@remotion/captions`` ``Caption`` type:

    {
      "text": str,
      "startMs": int,
      "endMs": int,
      "timestampMs": int | None,
      "confidence": float | None,
    }

Whitespace note: Remotion's ``createTikTokStyleCaptions`` is whitespace
sensitive. Each token's ``text`` should include a leading space for every
word except the first, so that pages render with correct spacing.
"""
from functools import lru_cache
from typing import Optional


@lru_cache(maxsize=1)
def _get_model(name: str, device: str, compute_type: str):
    # Imported lazily so that `python bot.py --help` stays fast.
    from faster_whisper import WhisperModel

    return WhisperModel(name, device=device, compute_type=compute_type)


def transcribe_audio(
    audio_path: str,
    model_name: str,
    device: str,
    compute_type: str,
    language: Optional[str] = None,
) -> tuple[list[dict], str]:
    """Return (captions, detected_language).

    Each caption is a Remotion ``Caption`` dict, ready to be serialized as
    JSON and passed to a Remotion composition.
    """
    model = _get_model(model_name, device, compute_type)
    segments, info = model.transcribe(
        audio_path,
        word_timestamps=True,
        language=language,
        vad_filter=True,
        beam_size=5,
    )

    captions: list[dict] = []
    first = True
    for segment in segments:
        if not segment.words:
            continue
        for w in segment.words:
            raw = w.word or ""
            stripped = raw.strip()
            if not stripped:
                continue

            start = float(w.start) if w.start is not None else 0.0
            end = float(w.end) if w.end is not None else start
            if end < start:
                end = start

            start_ms = int(round(start * 1000))
            end_ms = int(round(end * 1000))
            if end_ms <= start_ms:
                end_ms = start_ms + 1

            text = stripped if first else " " + stripped
            first = False

            confidence: Optional[float]
            probability = getattr(w, "probability", None)
            confidence = float(probability) if probability is not None else None

            captions.append(
                {
                    "text": text,
                    "startMs": start_ms,
                    "endMs": end_ms,
                    "timestampMs": start_ms,
                    "confidence": confidence,
                }
            )

    return captions, info.language
