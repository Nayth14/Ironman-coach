"""Tests for phase-aware strength prescription."""

from __future__ import annotations

from engine.models import AthleteProfile, ExperienceLevel, GoalType, PhaseName, Sport, StrengthBackground, StrengthEquipment
from engine import strength


def _profile(**overrides) -> AthleteProfile:
    base = dict(
        goal_type=GoalType.FINISH,
        race_name="Ironman Wales",
        race_date="2027-02-15",
        weekly_hours=10,
        limiter_discipline=Sport.SWIM,
        experience_level=ExperienceLevel.INTERMEDIATE,
        available_days=[0, 1, 2, 3, 5, 6],
        strength_background=StrengthBackground.INTERMEDIATE,
        strength_equipment=StrengthEquipment.MINIMAL,
    )
    base.update(overrides)
    return AthleteProfile.model_validate(base)


def test_taper_has_fewer_strength_sessions_than_base():
    profile = _profile()
    base_plan = strength.prescribe_for_week(profile, PhaseName.BASE, is_deload=False)
    taper_plan = strength.prescribe_for_week(profile, PhaseName.TAPER, is_deload=False)
    assert taper_plan.sessions_per_week <= base_plan.sessions_per_week


def test_deload_reduces_session_duration():
    profile = _profile()
    normal = strength.prescribe_for_week(profile, PhaseName.BASE, is_deload=False)
    deload = strength.prescribe_for_week(profile, PhaseName.BASE, is_deload=True)
    assert deload.session_duration_minutes < normal.session_duration_minutes


def test_taper_exercises_prefer_mobility():
    profile = _profile()
    taper_ex = strength.select_exercises(profile, PhaseName.TAPER)
    names = {e.name for e in taper_ex}
    assert "Plank" in names or "Dead bug" in names or "Bird dog" in names
