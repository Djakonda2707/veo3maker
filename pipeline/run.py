"""Run state — one reel = one directory under ``workspace/runs/<slug>/``.

    runs/<slug>/
        manifest.json     # hypothesis, character, segments, statuses
        frames/seg_NN.png # first frames
        clips/seg_NN.mp4  # animated clips
        raw.mp4           # assembled, no subtitles
        final.mp4         # after subtitles / packaging

The manifest is plain JSON on purpose: Claude Code (the orchestrator) can
read it, fill in segment prompts by editing it, and re-trigger generation
for just the segments that look broken.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from . import pconfig
from .models import Hypothesis, Segment


@dataclass
class Run:
    slug: str
    character: str
    character_ref: str
    hypothesis: Hypothesis
    segments: list[Segment] = field(default_factory=list)
    caption: str = ""
    cover_text: str = ""
    hashtags: list[str] = field(default_factory=list)
    music: str = ""
    created_at: str = ""

    # --- paths -------------------------------------------------------------
    @property
    def dir(self) -> Path:
        return pconfig.RUNS_DIR / self.slug

    @property
    def frames_dir(self) -> Path:
        return self.dir / "frames"

    @property
    def clips_dir(self) -> Path:
        return self.dir / "clips"

    @property
    def raw_path(self) -> Path:
        return self.dir / "raw.mp4"

    @property
    def final_path(self) -> Path:
        return self.dir / "final.mp4"

    def frame_path(self, index: int) -> Path:
        return self.frames_dir / f"seg_{index:02d}.png"

    def clip_path(self, index: int) -> Path:
        return self.clips_dir / f"seg_{index:02d}.mp4"

    # --- persistence -------------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "slug": self.slug,
            "character": self.character,
            "character_ref": self.character_ref,
            "hypothesis": self.hypothesis.to_dict(),
            "segments": [s.to_dict() for s in self.segments],
            "caption": self.caption,
            "cover_text": self.cover_text,
            "hashtags": self.hashtags,
            "music": self.music,
            "created_at": self.created_at,
        }

    def save(self) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        (self.dir / "manifest.json").write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def _manifest_path(slug: str) -> Path:
    return pconfig.RUNS_DIR / slug / "manifest.json"


def create_run(
    character_name: str,
    character_ref: str,
    hypothesis: Hypothesis,
    n_segments: int,
) -> Run:
    pconfig.ensure_dirs()
    slug = hypothesis.slug()
    run = Run(
        slug=slug,
        character=character_name,
        character_ref=character_ref,
        hypothesis=hypothesis,
        segments=[Segment(index=i, prompt="") for i in range(n_segments)],
        created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
    run.frames_dir.mkdir(parents=True, exist_ok=True)
    run.clips_dir.mkdir(parents=True, exist_ok=True)
    run.save()
    return run


def load_run(slug: str) -> Run:
    path = _manifest_path(slug)
    if not path.exists():
        raise FileNotFoundError(f"run '{slug}' not found at {path}")
    d = json.loads(path.read_text(encoding="utf-8"))
    hyp = Hypothesis(**d["hypothesis"])
    segs = [Segment(**s) for s in d.get("segments", [])]
    return Run(
        slug=d["slug"],
        character=d["character"],
        character_ref=d["character_ref"],
        hypothesis=hyp,
        segments=segs,
        caption=d.get("caption", ""),
        cover_text=d.get("cover_text", ""),
        hashtags=d.get("hashtags", []),
        music=d.get("music", ""),
        created_at=d.get("created_at", ""),
    )


def list_runs() -> list[str]:
    if not pconfig.RUNS_DIR.exists():
        return []
    return sorted(
        p.name for p in pconfig.RUNS_DIR.iterdir()
        if (p / "manifest.json").exists()
    )
