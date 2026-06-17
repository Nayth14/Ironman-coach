"""Tests for weekly context signal merging."""

from __future__ import annotations

from datetime import date

from engine.adaptation.loader import load_playbook
from engine.adaptation.signals import aggregate_signals
from engine.fixtures import load_fixture
from engine.models import PhaseName, PlanState, Sport, WeeklyContext, WorkoutCompletion


def _base_completions() -> list[WorkoutCompletion]:
    return [
        WorkoutCompletion(
            workout_id="w1",
            sport=Sport.RUN,
            completed=True,
            rpe=5,
            is_key_session=True,
            week_number=1,
            completed_at=date.today(),
        ),
        WorkoutCompletion(
            workout_id="w2",
            sport=Sport.BIKE,
            completed=True,
            rpe=5,
            is_key_session=False,
            week_number=1,
            completed_at=date.today(),
        ),
        WorkoutCompletion(
            workout_id="w3",
            sport=Sport.SWIM,
            completed=True,
            rpe=5,
            is_key_session=False,
            week_number=1,
            completed_at=date.today(),
        ),
    ]


def test_poor_sleep_adds_fatigue_flag():
    _, profile = load_fixture("beginner_first_im")
    spec = load_playbook().spec
    ctx = WeeklyContext(fatigue_flags=["poor sleep"], summary="Bad sleep week")

    signals = aggregate_signals(
        profile, _base_completions(), spec, weekly_context=ctx
    )

    assert any("poor sleep" in m for m in signals.flag_messages)


def test_life_stress_adds_flag():
    _, profile = load_fixture("beginner_first_im")
    spec = load_playbook().spec
    ctx = WeeklyContext(life_stress=True, summary="Work crunch")

    signals = aggregate_signals(
        profile, _base_completions(), spec, weekly_context=ctx
    )

    assert any("Life stress" in m for m in signals.flag_messages)


def test_illness_days_triggers_reentry():
    _, profile = load_fixture("beginner_first_im")
    spec = load_playbook().spec
    ctx = WeeklyContext(illness_days_off=4, summary="Flu")

    signals = aggregate_signals(
        profile, _base_completions(), spec, weekly_context=ctx
    )

    assert signals.illness_reentry is True
