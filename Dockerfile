# syntax=docker/dockerfile:1.6
#
# Subtitle bot image — Remotion-based pipeline.
#
# Two worlds in one container:
#   * Python 3.11 for the Telegram bot + faster-whisper transcription.
#   * Node 20 + Chromium for Remotion-based subtitle rendering.
#
# The bot.py process shells out to `npx remotion render` to produce the
# final video, so both runtimes need to be present.
#
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    NODE_MAJOR=20 \
    DEBIAN_FRONTEND=noninteractive

# System deps:
#   * ffmpeg for audio extraction and container probing
#   * libgomp1 for faster-whisper
#   * curl / ca-certificates / gnupg for the NodeSource apt key
#   * chromium + its runtime libs so Remotion can render headless
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        libgomp1 \
        ca-certificates \
        curl \
        gnupg \
        chromium \
        fonts-dejavu-core \
        fonts-noto-core \
        fonts-noto-color-emoji \
        libnss3 \
        libxss1 \
        libasound2 \
        libatk-bridge2.0-0 \
        libgtk-3-0 \
        libgbm1 \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key \
        | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_${NODE_MAJOR}.x nodistro main" \
        > /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Tell Remotion to use the system Chromium rather than downloading one.
ENV REMOTION_CHROME_EXECUTABLE=/usr/bin/chromium \
    PUPPETEER_SKIP_DOWNLOAD=1

WORKDIR /app

# ---- Python deps (cached independently of code) --------------------------
COPY requirements.txt ./
RUN pip install -r requirements.txt

# ---- Node deps for Remotion (cached independently of Python + source) ----
COPY remotion/package.json remotion/package-lock.json* ./remotion/
RUN cd remotion && npm install

# ---- Application source --------------------------------------------------
COPY . .

# Whisper model cache lives here; mount a volume to persist across restarts.
ENV HF_HOME=/app/.cache/huggingface \
    XDG_CACHE_HOME=/app/.cache

# tmp/ is writable at runtime.
RUN mkdir -p /app/tmp /app/.cache

CMD ["python", "-u", "bot.py"]
