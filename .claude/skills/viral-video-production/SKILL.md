---
name: viral-video-production
description: Produce a short viral reel from a fixed AI character — first frame (Nano Banana) → animate (Kling/Wan) → assemble → subtitles. Use when asked to "сделай ролик / вариацию", produce a reel for a character + hypothesis, or run the boont.ai-style production pipeline. Claude is the orchestrator; deterministic mechanics are `python -m pipeline.cli`.
metadata:
  tags: video, ai-video, pipeline, tiktok, reels, nano-banana, kling
---

## What this is

The production core of the "Виральный Рост" (boont.ai) system. **You (Claude
Code) are the orchestrator** — exactly as in the guide. You hold the context,
write the prompts, QC the frames with your own vision, and decide what to
regenerate. The heavy, deterministic work (calling image/video models,
ffmpeg assembly, subtitles) is done by `python -m pipeline.cli`.

Cost model: orchestration runs on the Claude subscription ($0 extra). Only
generation spends money (image relay + fal.ai). Everything runs in **mock
mode** (`PIPELINE_DRY_RUN=1`, the default) with zero spend until real keys
are set — use mock to dry-run the whole flow first.

## The unit of work

A **hypothesis** = `персонаж × формула × хук`. A long reel is built from
**~10-second segments**; each segment gets its own first frame and is then
animated. The same fixed character photo is fed into every first frame so the
creator looks identical across all reels and series — this is the key trick.

## Flow — do this

1. **Character.** Ensure the character exists (a fixed reference photo):
   ```bash
   python -m pipeline.cli character list
   python -m pipeline.cli character add --name NAME --photo PATH \
       --description "пол, возраст, стиль, вайб"
   ```

2. **Init a run** from the hypothesis (choose how many 10s segments):
   ```bash
   python -m pipeline.cli run init --character NAME \
       --persona "..." --formula "до/после|челлендж|explainer|..." \
       --hook "цепляющая фраза" --segments 4
   ```
   This prints a `slug` and a `manifest.json` path.

3. **Write the shot list.** Open `manifest.json` and, for each segment, fill:
   - `prompt` — what happens / is said in this 10s beat,
   - `first_frame_prompt` — a concrete image prompt for the starting frame
     (the character photo is added automatically as reference),
   - `motion_prompt` — how it should move for image→video.
   Keep the character description consistent across segments. Edit the file
   directly.

4. **Per segment: first frame → QC → animate.**
   ```bash
   python -m pipeline.cli first-frame --run SLUG --segment 0
   ```
   **Then Read the generated PNG** (`workspace/runs/SLUG/frames/seg_00.png`)
   and look at it. Hands/faces/text garbled? Wrong character? Re-run
   first-frame (tweak the prompt) before spending on animation. When the
   frame is clean:
   ```bash
   python -m pipeline.cli animate --run SLUG --segment 0
   ```
   Repeat for every segment. (In mock mode you can skip QC.)

5. **Assemble** the clips into one reel (optional background music):
   ```bash
   python -m pipeline.cli assemble --run SLUG --music PATH.mp3
   ```
   Output: `workspace/runs/SLUG/raw.mp4`.

6. **Subtitles (optional).** If there's a voiceover track with speech, burn
   animated captions via the existing Remotion presets:
   ```bash
   python -m pipeline.cli subtitles --run SLUG --voiceover VO.wav --preset hormozi
   ```
   Output: `final.mp4`. (Presets: hormozi / beast / neon / minimal.)

7. **Package.** Write the caption, cover text and hashtags yourself (you're
   good at this) and save them into `manifest.json` (`caption`, `cover_text`,
   `hashtags`). This is the "упаковка" step — no API needed.

### One-shot (mock / trusted prompts)

```bash
python -m pipeline.cli produce --run SLUG   # all frames + animate + assemble
python -m pipeline.cli status  --run SLUG
```

## Making a variation ("сделай вариацию")

Re-use the same character. Either init a new run with a different hook/formula,
or copy the manifest and change only the `*_prompt` fields, then re-run
`produce`. The fixed character ref keeps the creator identical — that's how a
series of 10–20 reels is produced.

## Switching from mock to real generation

Set in `.env` (see `.env.example`):
- `PIPELINE_DRY_RUN=0`
- `IMAGE_PROVIDER=relay`, `IMAGE_API_KEY=...` (laozhang.ai or Google OpenAI-compat)
- `VIDEO_PROVIDER=fal`, `FAL_API_KEY=...` (default model: Wan 2.5)

Nothing else changes — the same commands now hit real models.

## Notes

- Always Read frames before animating on real runs — animation is the
  expensive step; a bad frame wastes it.
- The manifest is the source of truth; regenerate individual segments by
  re-running `first-frame`/`animate` for just that index.
- See `PIPELINE.md` for architecture and the full stack/cost table.
