"""Speech-to-text with word-level timestamps via faster-whisper."""
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
    """Return (words, detected_language).

    Each word is a dict: {"text": str, "start": float, "end": float}.
    """
    model = _get_model(model_name, device, compute_type)
    segments, info = model.transcribe(
        audio_path,
        word_timestamps=True,
        language=language,
        vad_filter=True,
        beam_size=5,
    )

    words: list[dict] = []
    for segment in segments:
        if not segment.words:
            continue
        for w in segment.words:
            text = (w.word or "").strip()
            if not text:
                continue
            start = float(w.start) if w.start is not None else 0.0
            end = float(w.end) if w.end is not None else start
            if end < start:
                end = start
            words.append({"text": text, "start": start, "end": end})

    return words, info.language
