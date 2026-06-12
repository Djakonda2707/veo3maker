"""Thin clients for the external services from the guide's stack.

Each module exposes a tiny, typed surface and falls back to deterministic
offline mocks when ``pconfig.DRY_RUN`` is set or the relevant API key is
missing — so the orchestrator always runs end-to-end.
"""
