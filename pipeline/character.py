"""Character store — the fixed creator identity reused across all reels.

A character is a directory under ``workspace/characters/<name>/`` holding
the canonical photo (``ref.<ext>``), optional extra references, and a
``character.json`` with a textual description. Feeding the same photo into
every first frame is what keeps the AI creator looking identical, per the
guide.
"""
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from . import pconfig


@dataclass
class Character:
    name: str
    description: str = ""
    ref_image: str = ""                    # path to canonical photo
    extra_refs: list[str] = field(default_factory=list)

    @property
    def dir(self) -> Path:
        return pconfig.CHARACTERS_DIR / self.name

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "ref_image": self.ref_image,
            "extra_refs": self.extra_refs,
        }


def _meta_path(name: str) -> Path:
    return pconfig.CHARACTERS_DIR / name / "character.json"


def add_character(
    name: str, photo: str | Path, description: str = "",
    extra: list[str] | None = None,
) -> Character:
    pconfig.ensure_dirs()
    cdir = pconfig.CHARACTERS_DIR / name
    cdir.mkdir(parents=True, exist_ok=True)

    src = Path(photo)
    if not src.exists():
        raise FileNotFoundError(f"character photo not found: {src}")
    ref = cdir / f"ref{src.suffix.lower() or '.jpg'}"
    shutil.copyfile(src, ref)

    extra_paths: list[str] = []
    for i, e in enumerate(extra or []):
        ep = Path(e)
        if ep.exists():
            dst = cdir / f"extra_{i}{ep.suffix.lower() or '.jpg'}"
            shutil.copyfile(ep, dst)
            extra_paths.append(str(dst))

    char = Character(name=name, description=description,
                     ref_image=str(ref), extra_refs=extra_paths)
    _meta_path(name).write_text(
        json.dumps(char.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return char


def load_character(name: str) -> Character:
    meta = _meta_path(name)
    if not meta.exists():
        raise FileNotFoundError(
            f"character '{name}' not found. Add it with: "
            f"python -m pipeline.cli character add --name {name} --photo PATH"
        )
    d = json.loads(meta.read_text(encoding="utf-8"))
    return Character(**d)


def list_characters() -> list[str]:
    if not pconfig.CHARACTERS_DIR.exists():
        return []
    return sorted(
        p.name for p in pconfig.CHARACTERS_DIR.iterdir()
        if (p / "character.json").exists()
    )
