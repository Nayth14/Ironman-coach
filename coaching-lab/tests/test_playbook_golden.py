"""Golden scenario conformance tests from Playbook §10."""

from __future__ import annotations

from datetime import date

import pytest

from engine import adaptation
from engine.adaptation.loader import load_playbook
from engine.models import (
    AdaptationDecision,
    AthleteProfile,
    ExperienceLevel,
    GoalType,
    PhaseName,
    PlanState,
    Sport,
    StrengthBackground,
    StrengthEquipment,
    WorkoutCompletion,
)


def _profile(experience: ExperienceLevel = ExperienceLevel.INTERMEDIATE) -> AthleteProfile:
    return AthleteProfile(
        goal_type=GoalType.FINISH,
        race_name="Test IM",
        race_date=date(2026, 10, 1),
        weekly_hours=10.0,
        limiter_discipline=Sport.SWIM,
        experience_level=experience,
        available_days=[0, 1, 2, 3, 4, 5, 6],
    )


def _completion(**kwargs) -> WorkoutCompletion:
    sport = kwargs.pop("sport", Sport.RUN)
    return WorkoutCompletion(
        workout_id=kwargs.pop("workout_id", "w1"),
        sport=Sport(sport) if isinstance(sport, str) else sport,
        completed=kwargs.pop("completed", True),
        is_key_session=kwargs.pop("is_key", False),
        is_optional=kwargs.pop("is_optional", False),
        **kwargs,
    )


def test_g1_all_green_progress():
    completions = [
        _completion(workout_id="w1", rpe=5, readiness_score=8, is_key=True),
        _completion(workout_id="w2", sport=Sport.BIKE, rpe=6, readiness_score=7),
        _completion(workout_id="w3", sport=Sport.SWIM, rpe=5, readiness_score=8),
    ]
    result = adaptation.evaluate(_profile(), completions, phase=PhaseName.BASE)
    assert result.decision == AdaptationDecision.PROGRESS
    assert result.playbook_version


def test_g2_single_fatigue_hold():
    completions = [
        _completion(workout_id="w1", rpe=5, fatigue_flags=["poor sleep"]),
        _completion(workout_id="w2", rpe=5),
        _completion(workout_id="w3", rpe=6, is_key=True),
    ]
    result = adaptation.evaluate(_profile(), completions, phase=PhaseName.BASE)
    assert result.decision == AdaptationDecision.HOLD


def test_g3_stacked_flags_deload():
    completions = [
        _completion(workout_id="w1", rpe=9),
        _completion(workout_id="w2", rpe=8),
        _completion(workout_id="w3", rpe=9),
        _completion(workout_id="w4", rpe=7, readiness_score=3),
        _completion(workout_id="w5", rpe=6, readiness_score=4),
        _completion(workout_id="w6", fatigue_flags=["heavy legs"]),
    ]
    result = adaptation.evaluate(_profile(), completions, phase=PhaseName.BUILD)
    assert result.decision == AdaptationDecision.DELOAD


def test_g4_easy_rpe8_poor_sleep_hold_not_deload():
    completions = [
        _completion(workout_id="w1", sport=Sport.RUN, rpe=8),
        _completion(workout_id="w2", rpe=5, fatigue_flags=["poor sleep"]),
        _completion(workout_id="w3", rpe=6, is_key=True),
    ]
    result = adaptation.evaluate(_profile(), completions, phase=PhaseName.BASE)
    assert result.decision == AdaptationDecision.HOLD
    assert result.decision != AdaptationDecision.DELOAD


def test_g5_left_knee_bike_substitute():
    completions = [
        _completion(workout_id="w1", sport=Sport.RUN, fatigue_flags=["left knee"]),
        _completion(workout_id="w2", rpe=5, is_key=True),
        _completion(workout_id="w3", rpe=6),
    ]
    result = adaptation.evaluate(_profile(), completions, phase=PhaseName.BASE)
    assert result.decision == AdaptationDecision.BIKE_SUBSTITUTE


def test_g6_nausea_gut_training():
    completions = [
        _completion(workout_id="w1", sport=Sport.BIKE, fatigue_flags=["nausea"], is_key=True),
        _completion(workout_id="w2", rpe=5),
    ]
    result = adaptation.evaluate(_profile(), completions, phase=PhaseName.BUILD)
    assert result.decision == AdaptationDecision.GUT_TRAINING


def test_g7_consecutive_holds_escalate():
    state = PlanState(consecutive_holds=1)
    completions = [
        _completion(workout_id="w1", rpe=5, fatigue_flags=["poor sleep"]),
        _completion(workout_id="w2", rpe=6),
        _completion(workout_id="w3", rpe=5, is_key=True),
    ]
    result = adaptation.evaluate(
        _profile(), completions, plan_state=state, phase=PhaseName.BASE
    )
    assert result.decision == AdaptationDecision.DELOAD


def test_g10_taper_hold_only():
    completions = [
        _completion(workout_id="w1", rpe=5, fatigue_flags=["poor sleep"]),
        _completion(workout_id="w2", rpe=6, fatigue_flags=["heavy legs"]),
        _completion(workout_id="w3", rpe=5, is_key=True),
    ]
    result = adaptation.evaluate(_profile(), completions, phase=PhaseName.TAPER)
    assert result.decision == AdaptationDecision.HOLD
    assert result.decision != AdaptationDecision.PROGRESS


def test_g12_insufficient_data_hold():
    completions = [
        _completion(workout_id="w1", rpe=5),
        _completion(workout_id="w2", rpe=6),
    ]
    result = adaptation.evaluate(_profile(), completions, phase=PhaseName.BASE)
    assert result.decision == AdaptationDecision.HOLD
    assert result.insufficient_data


def test_g13_niggle_no_run_cap():
    completions = [
        _completion(workout_id="w1", sport=Sport.RUN, fatigue_flags=["shin"]),
        _completion(workout_id="w2", rpe=5, is_key=True),
        _completion(workout_id="w3", rpe=6),
    ]
    result = adaptation.evaluate(_profile(), completions, phase=PhaseName.BASE)
    assert result.decision == AdaptationDecision.BIKE_SUBSTITUTE
    assert "run_volume_cap" not in result.plan_state_delta


def test_g14_systemic_gut():
    completions = [
        _completion(workout_id="w1", sport=Sport.BIKE, fatigue_flags=["stomach"]),
        _completion(workout_id="w2", sport=Sport.RUN, fatigue_flags=["stomach"]),
        _completion(workout_id="w3", sport=Sport.SWIM, fatigue_flags=["stomach"]),
    ]
    result = adaptation.evaluate(_profile(), completions, phase=PhaseName.BUILD)
    assert result.decision == AdaptationDecision.GUT_TRAINING


def test_playbook_golden_ids_present():
    loaded = load_playbook()
    ids = {s.id for s in loaded.spec.golden_scenarios}
    for gid in [f"G{i}" for i in range(1, 15)]:
        assert gid in ids
