"""Viral content pipeline orchestrated by Claude Code.

Implements the system described in the "Виральный Рост" guide (boont.ai):
Research → hypothesis "blocks" (кубики) → production → packaging → analytics.

The production core mirrors the guide's flow:

    reference → first frame (Nano Banana) → check → animate (Kling)
    → inserts → check → assemble → subtitles → package

Every external service (ScrapeCreators, Gemini, Higgsfield) is a thin
provider with an offline mock so the whole orchestrator runs end-to-end
without API keys when ``PIPELINE_DRY_RUN=1`` (the default).
"""

__all__ = ["pconfig", "models"]
