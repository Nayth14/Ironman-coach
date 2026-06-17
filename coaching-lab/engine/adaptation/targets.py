"""Resolve which plan week is reviewed vs which receives micro-mutations."""

from __future__ import annotations

from collections import Counter

from engine.models import PlannedWeek, TrainingPlan, WorkoutCompletion


def week_by_number(plan: TrainingPlan, week_number: int) -> PlannedWeek | None:
    return next((w for w in plan.weeks if w.week_number == week_number), None)


def infer_reviewed_week_number(
    completions: list[WorkoutCompletion],
    plan: TrainingPlan | None = None,
) -> int:
    """Infer the plan week that feedback describes (mode week number wins)."""
    weeks = [c.week_number for c in completions if c.week_number is not None]
    if weeks:
        return Counter(weeks).most_common(1)[0][0]

    if plan:
        workout_week = {
            workout.id: planned_week.week_number
            for planned_week in plan.weeks
            for workout in planned_week.workouts
        }
        mapped = [
            workout_week[c.workout_id]
            for c in completions
            if c.workout_id in workout_week
        ]
        if mapped:
            return Counter(mapped).most_common(1)[0][0]

    return 1


def resolve_mutation_target_week(
    reviewed_week_number: int,
    plan: TrainingPlan | None,
) -> int | None:
    """Return the materialized week that receives workout mutations, if any."""
    target = reviewed_week_number + 1
    if not plan or not plan.weeks:
        return target
    materialized = {w.week_number for w in plan.weeks}
    return target if target in materialized else None
