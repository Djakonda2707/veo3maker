# Deploy: subtitle bot on Ubuntu via Docker

Tested on Ubuntu 20.04 / 22.04 / 24.04 (x86_64). For ARM just rebuild —
the Dockerfile is arch-agnostic.

## 1. Install Docker (skip if already installed)

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER"
# log out and back in so the group takes effect, or run: newgrp docker
```

Verify:

```bash
docker --version
docker compose version
```

## 2. Clone the repo

```bash
git clone https://github.com/djakonda2707/veo3maker.git
cd veo3maker
git checkout claude/telegram-video-subtitles-bot-AjydB
```

## 3. Configure environment

```bash
cp .env.example .env
nano .env
```

Fill in at minimum:

```ini
BOT_TOKEN=123456:ABCDEF...            # from @BotFather
WHISPER_MODEL=small                   # tiny/base/small/medium/large-v3
WHISPER_DEVICE=cpu                    # or "cuda" if the host has a GPU
WHISPER_COMPUTE_TYPE=int8             # int8 on CPU, float16 on GPU
WHISPER_LANGUAGE=                     # empty = auto-detect
MAX_VIDEO_SIZE_MB=20                  # Telegram Bot API limit
AUTO_DOWNLOAD_FONTS=1
```

Model sizing rule of thumb on CPU:

| Model     | RAM       | Speed (ref 1 min audio) |
|-----------|-----------|-------------------------|
| tiny      | ~1 GB     | very fast               |
| base      | ~1.5 GB   | fast                    |
| small     | ~2 GB     | balanced (default)      |
| medium    | ~4-5 GB   | slower                  |
| large-v3  | ~8-10 GB  | slow, highest quality   |

## 4. Build and start

```bash
docker compose build
docker compose up -d
docker compose logs -f
```

You should see:

```
... INFO subsbot: Generating preset previews...
... INFO subsbot: Starting bot, whisper=small device=cpu
... INFO aiogram.dispatcher: Start polling
```

## 5. Use the bot

1. Open the bot in Telegram, press **Start**.
2. Send a video (<= 20 MB due to Bot API limit).
3. Pick one of 6 styles from the preview grid.
4. Wait for the result — the bot transcribes, builds the ASS, burns
   subtitles into the video with ffmpeg and returns the MP4.

## Updating

```bash
cd veo3maker
git pull
docker compose build
docker compose up -d
```

## Troubleshooting

### Out of memory on `small` / `medium`
Drop `WHISPER_MODEL` to `base` or `tiny`, or increase swap.

### `Could not load fonts` in logs
The build step runs `download_fonts.py`. Rebuild: `docker compose build --no-cache`.

### Video > 20 MB
Telegram Bot API refuses to download files larger than 20 MB unless you
run a local Bot API server. Either ask the user to compress, or set up
https://github.com/tdlib/telegram-bot-api next to the bot and point it
at that server (not included in this repo yet).

### Free more space
```bash
docker system prune -af
docker volume ls  # whisper-cache holds the model weights
```

### Logs
```bash
docker compose logs -f                  # follow
docker compose logs --tail=200 subsbot  # last 200 lines
```

### Stop / restart
```bash
docker compose stop
docker compose restart
docker compose down          # stop + remove container
docker compose down -v       # also drop whisper-cache volume
```
