"""Command-line tools the Claude Code skill drives via Bash.

Design: the heavy, deterministic mechanics live here (generation, assembly);
the *judgement* — writing prompts, QC'ing frames, deciding regenerations —
is done by Claude Code between calls. Everything runs in mock mode with zero
spend until you set ``PIPELINE_DRY_RUN=0`` plus the relevant API keys.

Examples
--------
    python -m pipeline.cli character add --name alex --photo alex.jpg \
        --description "м, 28, кэжуал, дружелюбный"

    python -m pipeline.cli run init --character alex \
        --persona "уставший айтишник" --formula "до/после" \
        --hook "ты делаешь это неправильно" --segments 3

    # Claude fills segment prompts in manifest.json, then:
    python -m pipeline.cli first-frame --run SLUG --segment 0   # → Read PNG, QC
    python -m pipeline.cli animate     --run SLUG --segment 0
    python -m pipeline.cli assemble    --run SLUG
    python -m pipeline.cli produce     --run SLUG               # all-in-one
    python -m pipeline.cli status      --run SLUG
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys

from . import character as char_store
from . import pconfig, production
from .assembly import burn_subtitles, concat_clips
from .models import Hypothesis
from .run import create_run, list_runs, load_run


def _print(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


# --- character -------------------------------------------------------------
def cmd_character_add(a) -> int:
    c = char_store.add_character(
        a.name, a.photo, description=a.description or "", extra=a.extra or []
    )
    _print({"ok": True, "character": c.to_dict()})
    return 0


def cmd_character_list(_a) -> int:
    _print({"characters": char_store.list_characters()})
    return 0


# --- run lifecycle ---------------------------------------------------------
def cmd_run_init(a) -> int:
    char = char_store.load_character(a.character)
    hyp = Hypothesis(
        character=a.persona or char.description or a.character,
        formula=a.formula,
        hook=a.hook,
        script=a.script or "",
    )
    run = create_run(char.name, char.ref_image, hyp, a.segments)
    _print({
        "ok": True,
        "slug": run.slug,
        "manifest": str(run.dir / "manifest.json"),
        "note": "Заполни prompt / first_frame_prompt / motion_prompt по сегментам "
                "в manifest.json, затем запусти first-frame / animate / produce.",
    })
    return 0


def cmd_run_list(_a) -> int:
    _print({"runs": list_runs()})
    return 0


def cmd_status(a) -> int:
    run = load_run(a.run)
    segs = []
    for s in run.segments:
        segs.append({
            "index": s.index,
            "has_prompt": bool(s.prompt or s.first_frame_prompt),
            "frame": run.frame_path(s.index).exists(),
            "clip": run.clip_path(s.index).exists(),
        })
    _print({
        "slug": run.slug,
        "character": run.character,
        "segments": segs,
        "raw": run.raw_path.exists(),
        "final": run.final_path.exists(),
        "dry_run": pconfig.DRY_RUN,
    })
    return 0


# --- generation ------------------------------------------------------------
def cmd_first_frame(a) -> int:
    run = load_run(a.run)
    path = asyncio.run(production.make_first_frame(run, a.segment))
    _print({"ok": True, "segment": a.segment, "frame": str(path),
            "next": "Прочитай PNG глазами; если артефакты — перегенери, иначе animate."})
    return 0


def cmd_animate(a) -> int:
    run = load_run(a.run)
    path = asyncio.run(production.animate_segment(run, a.segment))
    _print({"ok": True, "segment": a.segment, "clip": str(path)})
    return 0


def cmd_produce(a) -> int:
    run = load_run(a.run)
    clips = asyncio.run(production.produce_all(run))
    raw = concat_clips(run, music=run.music or None)
    _print({"ok": True, "clips": [str(c) for c in clips], "raw": str(raw)})
    return 0


def cmd_assemble(a) -> int:
    run = load_run(a.run)
    raw = concat_clips(run, music=a.music or run.music or None)
    _print({"ok": True, "raw": str(raw)})
    return 0


def cmd_subtitles(a) -> int:
    run = load_run(a.run)
    final = asyncio.run(burn_subtitles(run, a.voiceover, preset=a.preset))
    _print({"ok": True, "final": str(final)})
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="pipeline.cli", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    ch = sub.add_parser("character", help="manage characters")
    chs = ch.add_subparsers(dest="sub", required=True)
    a = chs.add_parser("add")
    a.add_argument("--name", required=True)
    a.add_argument("--photo", required=True)
    a.add_argument("--description", default="")
    a.add_argument("--extra", nargs="*", default=[])
    a.set_defaults(func=cmd_character_add)
    chs.add_parser("list").set_defaults(func=cmd_character_list)

    r = sub.add_parser("run", help="manage runs")
    rs = r.add_subparsers(dest="sub", required=True)
    ri = rs.add_parser("init")
    ri.add_argument("--character", required=True)
    ri.add_argument("--persona", default="")
    ri.add_argument("--formula", required=True)
    ri.add_argument("--hook", required=True)
    ri.add_argument("--script", default="")
    ri.add_argument("--segments", type=int, default=3)
    ri.set_defaults(func=cmd_run_init)
    rs.add_parser("list").set_defaults(func=cmd_run_list)

    s = sub.add_parser("status"); s.add_argument("--run", required=True)
    s.set_defaults(func=cmd_status)

    ff = sub.add_parser("first-frame")
    ff.add_argument("--run", required=True)
    ff.add_argument("--segment", type=int, required=True)
    ff.set_defaults(func=cmd_first_frame)

    an = sub.add_parser("animate")
    an.add_argument("--run", required=True)
    an.add_argument("--segment", type=int, required=True)
    an.set_defaults(func=cmd_animate)

    pr = sub.add_parser("produce"); pr.add_argument("--run", required=True)
    pr.set_defaults(func=cmd_produce)

    asm = sub.add_parser("assemble")
    asm.add_argument("--run", required=True)
    asm.add_argument("--music", default="")
    asm.set_defaults(func=cmd_assemble)

    st = sub.add_parser("subtitles")
    st.add_argument("--run", required=True)
    st.add_argument("--voiceover", required=True)
    st.add_argument("--preset", default="")
    st.set_defaults(func=cmd_subtitles)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:  # surface a clean error to the skill
        _print({"ok": False, "error": str(exc), "type": type(exc).__name__})
        return 1


if __name__ == "__main__":
    sys.exit(main())
