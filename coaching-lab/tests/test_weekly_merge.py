"""Tests for weekly context merge helper."""

from __future__ import annotations

from engine.adaptation.weekly_merge import merge_weekly_context
from engine.models import WeeklyContext


def test_merge_combines_flags_and_illness():
    base = WeeklyContext(
        summary="base",
        fatigue_flags=["poor sleep"],
        illness_days_off=2,
    )
    aug = WeeklyContext(
        summary="augmented",
        fatigue_flags=["left knee"],
        illness_days_off=4,
        life_stress=True,
    )
    merged = merge_weekly_context(base, aug)
    assert merged is not None
    assert "poor sleep" in merged.fatigue_flags
    assert "left knee" in merged.fatigue_flags
    assert merged.illness_days_off == 4
    assert merged.life_stress is True
    assert merged.summary == "augmented"
