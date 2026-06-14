"""Tests for workout step enrichment fallback."""

from __future__ import annotations

from engine.enrich import enrich_week_steps, template_steps_for_workout
from engine.models import (
    AthleteProfile,
    ExperienceLevel,
    GoalType,
    PhaseName,
    PlannedWeek,
    PurposeTag,
    Sport,
    StrengthExercise,
    Workout,
    WorkoutStatus,
    WorkoutStepType,
)


def _profile() -> AthleteProfile:
    return AthleteProfile.model_validate(
        {
            "goal_type": "finish",
            "race_name": "Ironman Wales",
            "race_date": "2027-02-15",
            "weekly_hours": 9,
            "limiter_discipline": "swim",
            "experience_level": ExperienceLevel.BEGINNER.value,
            "available_days": [0, 1, 2, 3, 5, 6],
        }
    )


def test_template_endurance_has_warmup_work_cooldown():
    workout = Workout(
        id="run1",
        sport=Sport.RUN,
        title="Long run",
        purpose_tag=PurposeTag.AEROBIC_BASE,
        estimated_duration_seconds=5400,
        status=WorkoutStatus.PLANNED,
    )
    steps = template_steps_for_workout(workout)
    types = {s.type for s in steps}
    assert WorkoutStepType.WARMUP in types
    assert WorkoutStepType.WORK in types
    assert WorkoutStepType.COOLDOWN in types
    total = sum(s.duration_seconds or 0 for s in steps)
    assert 4500 <= total <= 6300


def test_parse_steps_coerces_notes_type():
    from engine.enrich import _parse_steps

    steps = _parse_steps(
        [
            {
                "id": "s1",
                "type": "notes",
                "name": "Remember to fuel every 20 min",
                "duration_seconds": 60,
            }
        ]
    )
    assert len(steps) == 1
    assert steps[0].type.value == "work"
    assert "fuel" in (steps[0].notes or steps[0].name or "")


def test_enrich_week_without_api_key_uses_fallback(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    week = PlannedWeek(
        week_number=1,
        phase=PhaseName.PREP,
        target_hours=9.0,
        workouts=[
            Workout(
                id="bike1",
                sport=Sport.BIKE,
                title="Long ride",
                day_of_week=5,
                purpose_tag=PurposeTag.AEROBIC_BASE,
                is_key_session=True,
                estimated_duration_seconds=7200,
                status=WorkoutStatus.PLANNED,
            ),
            Workout(
                id="str1",
                sport=Sport.STRENGTH,
                title="Strength session",
                day_of_week=3,
                purpose_tag=PurposeTag.STRENGTH,
                estimated_duration_seconds=1800,
                exercises=[
                    StrengthExercise(name="Plank", sets=3, reps="30s"),
                ],
                status=WorkoutStatus.PLANNED,
            ),
        ],
    )
    result = enrich_week_steps(week, _profile(), PhaseName.PREP)
    for w in result.workouts:
        assert len(w.steps) >= 3
        total = sum(s.duration_seconds or 0 for s in w.steps)
        assert total > 0
