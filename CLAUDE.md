# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Telegram bot that overlays animated TikTok/Reels-style subtitles onto user-uploaded videos. The pipeline is: Telegram upload → ffmpeg extracts audio → `faster-whisper` produces word-level captions → `npx remotion render` composites the original video with a styled caption track → bot replies with the rendered mp4.

Two runtimes live in a single container/host:
- **Python 3.11** — the aiogram bot (`bot.py`) and transcription (`transcribe.py`).
- **Node 20 + headless Chromium** — Remotion 4 compositions under `remotion/`.

The Python side shells out to `npx remotion render` (see `render_remotion.py`); there is no HTTP bridge between them.

## Common commands

### Native dev loop

```bash
bash scripts/install.sh          # apt deps + .venv + npm install inside remotion/
nano .env                        # set BOT_TOKEN (copy from .env.example)
bash scripts/run.sh              # launches bot.py in a detached tmux session 'subsbot'
tmux attach -t subsbot           # watch live logs
tail -f /tmp/subsbot.log
```

Run the bot directly (without tmux):

```bash
. .venv/bin/activate
python -u bot.py
```

### Remotion compositions

```bash
cd remotion
npm run dev          # Remotion Studio at http://localhost:3000 for visual preview
npm run build        # produce a bundle (rarely needed — render.py uses `npx remotion render`)
```

Render a composition manually (matches how `render_remotion.py` invokes it):

```bash
cd remotion
npx remotion render CaptionedVideo /tmp/out.mp4 --props=/tmp/props.json --concurrency=1 --codec=h264
```

`props.json` must match `captionedVideoSchema` in `remotion/src/CaptionedVideo/schema.ts` (`videoSrc`, `captions`, `presetKey`, `durationInSeconds`, `fps`).

### Docker

```bash
docker compose up -d --build
docker compose logs -f subsbot
docker compose exec subsbot chromium --version   # sanity-check headless browser
```

The `whisper-cache` and `subsbot-tmp` named volumes persist the Whisper model download and in-flight work dirs.

## Architecture

### End-to-end request flow (`bot.py`)

1. `handle_video` (aiogram `F.video | F.video_note | F.document`) enforces `MAX_VIDEO_SIZE_MB` (Telegram Bot API hard-limits downloads to 20 MB unless a local Bot API server is used), downloads into `tmp/<user_id>_<msg_id>/input.mp4`, and stores the path in FSM state `VideoStates.choosing_style`.
2. Inline keyboard from `_build_presets_keyboard` lets the user pick one of four presets. The callback handler `on_style` clears the FSM state immediately so double-clicks don't launch a second pipeline.
3. Pipeline (in `on_style`): `extract_audio` (`render.py`) → `transcribe_audio` via `asyncio.to_thread` (`transcribe.py`) → `probe_duration` → `render_captioned_video` (`render_remotion.py`) → `answer_video` with the rendered mp4.
4. `_cleanup` wipes the per-job work dir in a `finally` block. `_startup` also wipes `TMP_ROOT` on boot so orphans from a previous crash don't accumulate.
5. All user-facing strings are in Russian.

### Caption data contract

`transcribe_audio` returns a list of dicts that match the `@remotion/captions` `Caption` type:

```
{ "text": str, "startMs": int, "endMs": int, "timestampMs": int|None, "confidence": float|None }
```

**Whitespace rule:** every token's `text` starts with a leading space *except the first*. `@remotion/captions.createTikTokStyleCaptions` is whitespace-sensitive — breaking this makes pages concatenate words without gaps.

`render_remotion.py` serializes these dicts to a temp `*.props.json` alongside the output path and passes `--props=<file>` to avoid shell-escaping giant caption arrays. The file is deleted in a `finally` block.

### Preset synchronization

Preset keys MUST stay in sync across three places:

- `PRESETS` tuple in `bot.py` (keys + Russian titles shown in the keyboard)
- `PRESET_KEYS` in `remotion/src/CaptionedVideo/schema.ts` (Zod enum — validation fails otherwise)
- `STYLE_MAP` in `remotion/src/CaptionedVideo/CaptionPage.tsx` (wires a key to a style component)

Adding a preset requires editing all three plus a new component under `remotion/src/CaptionedVideo/styles/`.

### Remotion composition layout

- `remotion/src/index.ts` → `registerRoot(RemotionRoot)`.
- `remotion/src/Root.tsx` declares the single `CaptionedVideo` composition (1080×1920, 30 fps default). `calculateMetadata` derives `durationInFrames` from the `durationInSeconds` prop, so the composition auto-sizes to each incoming video.
- `remotion/src/CaptionedVideo/index.tsx` uses `createTikTokStyleCaptions({ combineTokensWithinMilliseconds: 1200 })` to group word tokens into pages, then emits one `<Sequence>` per page wrapping `<CaptionPage>`.
- `CaptionPage.tsx` computes `enterProgress` (150 ms ease-in) and dispatches to a style component via `STYLE_MAP[presetKey]`. Caption positioning (`paddingBottom: "18%"`, centered) lives here, not in individual styles.
- Style components under `styles/` are pure presentational React — they receive `{ page, absoluteTimeMs, enterProgress }` and should not mutate state or fetch.

The entry point is fixed by `Config.setEntryPoint("src/index.ts")` in `remotion.config.ts`, so `render_remotion.py` intentionally does not pass an entry file to the CLI.

### Config

`config.py` reads `.env` via `python-dotenv` and raises at import time if `BOT_TOKEN` is missing. `TMP_ROOT` is `./tmp`, `REMOTION_ROOT` is `./remotion`. Whisper knobs (`WHISPER_MODEL`, `WHISPER_DEVICE`, `WHISPER_COMPUTE_TYPE`, `WHISPER_LANGUAGE`) and `MAX_VIDEO_SIZE_MB` are all environment-driven.

The `WhisperModel` in `transcribe.py` is wrapped in `@lru_cache(maxsize=1)` and imported lazily, so the first transcription pays the model-load cost and `bot.py --help` stays fast.

## Conventions to preserve

- **Russian user copy.** All bot-facing strings (welcome, errors, buttons) are in Russian. Match the existing tone when adding messages.
- **Concurrency 1.** Remotion is invoked with `--concurrency=1` and `Config.setConcurrency(1)` so a render fits in ~1.5 GB RAM. Do not raise this without also raising the compose memory limit.
- **System Chromium.** `Dockerfile` sets `REMOTION_CHROME_EXECUTABLE=/usr/bin/chromium` and `PUPPETEER_SKIP_DOWNLOAD=1`. Don't introduce code that assumes a bundled browser.
- **Long-polling only.** No webhook/inbound ports — only outbound HTTPS to `api.telegram.org` is required.
- **Error classes.** `FFmpegError` (`render.py`) and `RemotionError` (`render_remotion.py`) tail the last 2–4 KB of stderr. The bot formats these into `<pre>` blocks via `_tail()`; preserve that pattern when adding subprocess wrappers.
