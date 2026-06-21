from __future__ import annotations

from engine.models import PurposeTag, Sport, Workout, WorkoutStatus, WorkoutStepType
from engine.workout_bank.expand import expand_bank_workout_steps


def test_expand_long_run_race_blocks_from_bank_template():
    workout = Workout(
        id="run-long",
        sport=Sport.RUN,
        title="Long run",
        purpose_tag=PurposeTag.RACE_EXECUTION,
        is_key_session=True,
        estimated_duration_seconds=120 * 60,
        bank_workout_id="LR120-2",
        status=WorkoutStatus.PLANNED,
    )
    steps = expand_bank_workout_steps(workout)
    assert steps is not None
    assert [s.type for s in steps] == [
        WorkoutStepType.WARMUP,
        WorkoutStepType.WORK,
        WorkoutStepType.COOLDOWN,
    ]
    assert "LR120-2" in (steps[1].notes or "")
    assert "RP" in (steps[1].notes or "")


def test_expand_long_run_conversational_is_easy_target():
    workout = Workout(
        id="run-easy-long",
        sport=Sport.RUN,
        title="Long run",
        purpose_tag=PurposeTag.AEROBIC_BASE,
        is_key_session=True,
        estimated_duration_seconds=150 * 60,
        bank_workout_id="LR150-1",
        status=WorkoutStatus.PLANNED,
    )
    steps = expand_bank_workout_steps(workout)
    assert steps is not None
    assert (steps[1].target.label or "").startswith("Easy")
