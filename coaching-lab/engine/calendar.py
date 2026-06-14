"""Calendar date assignment for training plans."""

from __future__ import annotations

from datetime import date, timedelta

from engine.models import PlannedWeek, Workout


def plan_start_date(today: date) -> date:
    """Next Monday on or after today (Mon=weekday 0)."""
    days_until_monday = (7 - today.weekday()) % 7
    return today if days_until_monday == 0 else today + timedelta(days=days_until_monday)


def workout_date(plan_start: date, week_number: int, day_of_week: int) -> date:
    """Map week number + day_of_week (0=Mon..6=Sun) to a calendar date."""
    return plan_start + timedelta(days=(week_number - 1) * 7 + day_of_week)


def assign_dates(week: PlannedWeek, plan_start: date) -> None:
    """Set scheduled_date on every workout in the week."""
    for workout in week.workouts:
        if workout.day_of_week is not None:
            workout.scheduled_date = workout_date(
                plan_start, week.week_number, workout.day_of_week
            )


def assign_dates_to_workouts(
    workouts: list[Workout], plan_start: date, week_number: int
) -> None:
    """Assign dates to a flat workout list (e.g. when loading from DB)."""
    for workout in workouts:
        if workout.day_of_week is not None:
            workout.scheduled_date = workout_date(
                plan_start, week_number, workout.day_of_week
            )
