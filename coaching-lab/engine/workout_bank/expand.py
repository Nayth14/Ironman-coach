from __future__ import annotations

import uuid

from engine.models import PurposeTag, Sport, TargetType, Workout, WorkoutStep, WorkoutStepType, WorkoutTarget
from engine.workout_bank.load import get_bank_workout


def _new_step_id() -> str:
    return uuid.uuid4().hex[:12]


def _rpe_target(purpose: PurposeTag) -> WorkoutTarget:
    if purpose in (PurposeTag.THRESHOLD, PurposeTag.VO2):
        return WorkoutTarget(type=TargetType.RPE, min=7, max=8, label="Threshold RPE 7-8")
    if purpose in (PurposeTag.RACE_EXECUTION, PurposeTag.DURABILITY):
        return WorkoutTarget(type=TargetType.RPE, min=6, max=7, label="Race pace RPE 6-7")
    return WorkoutTarget(type=TargetType.RPE, min=2, max=4, label="Easy RPE 2-4")


def _default_warmup_cooldown(workout: Workout) -> tuple[int, int]:
    total = workout.estimated_duration_seconds or 3600
    if workout.sport == Sport.RUN and total <= 3000:
        return 12 * 60, 8 * 60
    if total <= 3000:
        return 10 * 60, 5 * 60
    if total <= 4200:
        return 12 * 60, 8 * 60
    return 15 * 60, 10 * 60


def expand_bank_workout_steps(workout: Workout) -> list[WorkoutStep] | None:
    entry = get_bank_workout(workout.bank_workout_id)
    if not entry:
        return None

    total = workout.estimated_duration_seconds or entry.duration_minutes * 60
    warm, cool = _default_warmup_cooldown(workout)
    if entry.warmup_minutes is not None:
        warm = entry.warmup_minutes * 60
    if entry.cooldown_minutes is not None:
        cool = entry.cooldown_minutes * 60
    warm = min(warm, max(300, total // 3))
    cool = min(cool, max(300, total // 3))
    work = max(600, total - warm - cool)

    note_parts = [f"Bank template {entry.id}", entry.main_set]
    if entry.intensity_hint:
        note_parts.append(f"Intensity: {entry.intensity_hint}")
    if workout.fueling_notes:
        note_parts.append(workout.fueling_notes)

    return [
        WorkoutStep(
            id=_new_step_id(),
            type=WorkoutStepType.WARMUP,
            name="Warm up",
            duration_seconds=warm,
            target=WorkoutTarget(type=TargetType.RPE, min=2, max=3, label="Easy RPE 2-3"),
        ),
        WorkoutStep(
            id=_new_step_id(),
            type=WorkoutStepType.WORK,
            name=entry.title,
            duration_seconds=work,
            target=_rpe_target(workout.purpose_tag),
            notes="; ".join(note_parts),
        ),
        WorkoutStep(
            id=_new_step_id(),
            type=WorkoutStepType.COOLDOWN,
            name="Cool down",
            duration_seconds=cool,
            target=WorkoutTarget(type=TargetType.RPE, min=1, max=2, label="Very easy RPE 1-2"),
        ),
    ]
