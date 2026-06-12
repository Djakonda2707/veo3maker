"""Dataclasses passed between pipeline stages.

These map directly onto the guide's vocabulary:

* ``Reel`` / ``Account``     — raw research scraped by ScrapeCreators.
* ``VideoAnalysis``          — what Gemini Flash Lite "sees" in a reel.
* ``Block`` (кубик)          — a reusable element Claude extracts:
                               visual formula, text hook, meaning formula,
                               or character.
* ``Hypothesis``             — персонаж × формула × хук, the unit we test.
* ``Segment`` / ``ClipPlan`` — a 10s piece and the full shot list.
* ``Metrics``                — analytics pulled back after publishing.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any


class Platform(str, Enum):
    tiktok = "tiktok"
    instagram = "instagram"
    youtube = "youtube"


class BlockKind(str, Enum):
    visual_formula = "visual_formula"   # как начинается, как подаётся
    text_hook = "text_hook"             # цепляющая фраза/текст на экране
    meaning_formula = "meaning_formula"  # до/после, челлендж, explainer...
    character = "character"             # персонаж / портрет AI-креатора


def _ser(obj: Any) -> Any:
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, list):
        return [_ser(x) for x in obj]
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    return obj


@dataclass
class Reel:
    platform: Platform
    url: str
    author: str
    views: int = 0
    likes: int = 0
    comments_count: int = 0
    caption: str = ""
    posted_at: str | None = None
    top_comments: list[str] = field(default_factory=list)

    @property
    def engagement(self) -> float:
        if self.views <= 0:
            return 0.0
        return (self.likes + self.comments_count) / self.views

    def to_dict(self) -> dict:
        d = asdict(self)
        d["platform"] = self.platform.value
        d["engagement"] = round(self.engagement, 4)
        return d


@dataclass
class Account:
    platform: Platform
    handle: str
    followers: int = 0
    niche: str = ""
    reels: list[Reel] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "platform": self.platform.value,
            "handle": self.handle,
            "followers": self.followers,
            "niche": self.niche,
            "reels": [r.to_dict() for r in self.reels],
        }


@dataclass
class VideoAnalysis:
    """What Gemini Flash Lite extracts from a single reel (cheap, fast)."""
    url: str
    hook: str = ""           # first 1-2s: what grabs attention
    visual: str = ""         # framing, pacing, setting
    script: str = ""         # spoken / on-screen narrative
    format: str = ""         # до/после, челлендж, explainer, ...
    character: str = ""      # who fronts it (gender/age/vibe)
    why_it_works: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Block:
    """A reusable "кубик" Claude lifts from many analyses."""
    kind: BlockKind
    text: str
    seen_count: int = 1
    examples: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["kind"] = self.kind.value
        return d


@dataclass
class Hypothesis:
    """персонаж × формула × хук — the thing a weekly sprint actually tests."""
    character: str
    formula: str
    hook: str
    script: str = ""
    notes: str = ""

    def slug(self) -> str:
        import re

        base = f"{self.character}-{self.formula}-{self.hook}".lower()
        return re.sub(r"[^a-z0-9]+", "-", base).strip("-")[:60] or "hypothesis"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Segment:
    """One ~10s piece of the final video."""
    index: int
    prompt: str                       # what happens / is said
    first_frame_prompt: str = ""      # image prompt for Nano Banana
    motion_prompt: str = ""           # image→video prompt for Kling
    first_frame_path: str | None = None
    clip_path: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ClipPlan:
    hypothesis: Hypothesis
    character_ref: str                # path to the fixed character photo
    segments: list[Segment] = field(default_factory=list)
    caption: str = ""
    cover_text: str = ""
    hashtags: list[str] = field(default_factory=list)
    music: str = ""

    def to_dict(self) -> dict:
        return {
            "hypothesis": self.hypothesis.to_dict(),
            "character_ref": self.character_ref,
            "segments": [s.to_dict() for s in self.segments],
            "caption": self.caption,
            "cover_text": self.cover_text,
            "hashtags": self.hashtags,
            "music": self.music,
        }


@dataclass
class Metrics:
    url: str
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    pulled_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
