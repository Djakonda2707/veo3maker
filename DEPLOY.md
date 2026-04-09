# Deployment

The bot ships as a single Docker image that bundles:

* Python 3.11 + `aiogram` + `faster-whisper` (the Telegram bot + transcription)
* Node 20 + headless Chromium + Remotion 4 (the rendering engine)
* `ffmpeg` (audio extraction, probing)

## 1. Requirements

* Ubuntu 22.04 / 24.04 x86_64 (or any Linux host with Docker)
* At least **2 CPU cores** and **3.5 GB RAM** — Remotion + Whisper `small` model fit comfortably
* No GPU required
* Docker Engine 24+ and the Compose plugin (`docker compose`, not the legacy `docker-compose`)

### Installing Docker on a fresh Ubuntu host

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER"
newgrp docker
```

## 2. Clone and configure

```bash
git clone https://github.com/djakonda2707/veo3maker.git
cd veo3maker
cp .env.example .env
nano .env   # paste your BOT_TOKEN
```

Required environment variables:

| Variable | Example | Notes |
|---|---|---|
| `BOT_TOKEN` | `12345:ABCDEF...` | From [@BotFather](https://t.me/BotFather) |
| `WHISPER_MODEL` | `small` | `tiny` / `base` / `small` / `medium` / `large-v3` |
| `WHISPER_DEVICE` | `cpu` | Only `cpu` is supported on GPU-less hosts |
| `WHISPER_COMPUTE_TYPE` | `int8` | `int8` is fastest on CPU |
| `WHISPER_LANGUAGE` | *(empty)* | Leave empty for auto-detect |
| `MAX_VIDEO_SIZE_MB` | `20` | Telegram Bot API file-download limit |

## 3. Build and run

```bash
docker compose up -d --build
docker compose logs -f subsbot
```

The first run will:

1. Build the image (pulls Node, Chromium, ffmpeg — ~1.5 GB)
2. `npm install` inside `remotion/` (cached in the image)
3. Download the selected `faster-whisper` model into the `whisper-cache` volume (~240 MB for `small`)

Subsequent restarts are fast.

## 4. Updating

```bash
git pull
docker compose up -d --build
```

The Whisper model cache and the bot's temporary workdir (`subsbot-tmp`) are preserved as named volumes, so updates do not re-download the model.

## 5. Troubleshooting

**Chromium can't start inside the container**

Remotion uses the system Chromium installed in the image (`/usr/bin/chromium`). If you see "Failed to launch the browser process", check that:

```bash
docker compose exec subsbot chromium --version
```

returns a version. The image sets `REMOTION_CHROME_EXECUTABLE=/usr/bin/chromium`, so Remotion should not attempt to download its own copy.

**Out of memory during render**

Remotion renders single-threaded in this project (`concurrency=1`) so it fits in ~1.5 GB. If you still OOM:

* Use a smaller Whisper model (`tiny` or `base`)
* Lower `MAX_VIDEO_SIZE_MB` so users can't submit huge clips
* Bump the compose `deploy.resources.limits.memory` if your host has more RAM

**`TelegramNetworkError: Cannot connect to host api.telegram.org`**

Your host can't reach Telegram. Check DNS and firewall. This bot uses long-polling, no inbound ports required — only outbound HTTPS to `api.telegram.org`.
