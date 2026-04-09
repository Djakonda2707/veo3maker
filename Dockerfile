# syntax=docker/dockerfile:1.6
#
# Subtitle bot image.
#
# * python:3.11-slim base — small and ships the CPython we need.
# * ffmpeg + libass are installed from apt for the subtitles filter.
# * fonts are downloaded at build time so container cold start is fast
#   and we do not need outbound GitHub access on every restart.
#
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System deps: ffmpeg/libass for burn-in, libgomp for faster-whisper,
# ca-certificates so urllib can reach GitHub for the OFL fonts.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        libgomp1 \
        ca-certificates \
        fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install python deps first so they get cached independently of code changes.
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copy source.
COPY . .

# Pre-download OFL fonts into the image so runtime does not need network.
RUN python download_fonts.py || true

# Whisper model cache lives here; mount a volume to persist across restarts.
ENV HF_HOME=/app/.cache/huggingface \
    XDG_CACHE_HOME=/app/.cache

# tmp/ and previews/ are writable at runtime.
RUN mkdir -p /app/tmp /app/previews /app/.cache

CMD ["python", "-u", "bot.py"]
