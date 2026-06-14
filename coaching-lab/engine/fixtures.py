"""Load saved athlete personas for regression testing.

Lets us re-run the same profiles through the engine after rule changes and
compare output, without going through the chat each time.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from engine.models import AthleteProfile

_FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def list_fixtures() -> list[str]:
    return sorted(p.stem for p in _FIXTURE_DIR.glob("*.yaml"))


def load_fixture(stem: str) -> tuple[str, AthleteProfile]:
    path = _FIXTURE_DIR / f"{stem}.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    name = data.get("name", stem)
    profile = AthleteProfile.model_validate(data["profile"])
    return name, profile
