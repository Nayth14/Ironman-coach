"""Prompt templates for the coaching engine.

Kept separate from logic so we can iterate on wording without touching rules.
These port to `packages/llm` in the main app.
"""

from pathlib import Path

_PROMPT_DIR = Path(__file__).parent


def _load(name: str) -> str:
    return (_PROMPT_DIR / name).read_text(encoding="utf-8")


ONBOARDING_SYSTEM = _load("onboarding_system.md")
COACHING_SYSTEM = _load("coaching_system.md")
EXTRACTION_SYSTEM = _load("extraction_system.md")
SUMMARY_SYSTEM = _load("summary_system.md")
WORKOUT_STEPS_SYSTEM = _load("workout_steps_system.md")

__all__ = [
    "ONBOARDING_SYSTEM",
    "COACHING_SYSTEM",
    "EXTRACTION_SYSTEM",
    "SUMMARY_SYSTEM",
    "WORKOUT_STEPS_SYSTEM",
]
