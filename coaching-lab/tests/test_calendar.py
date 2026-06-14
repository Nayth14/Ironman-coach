"""Tests for calendar date assignment."""

from __future__ import annotations

from datetime import date

from engine.calendar import assign_dates, plan_start_date, workout_date
from engine.models import PhaseName, PlannedWeek, Sport, Workout, WorkoutStatus, PurposeTag


def test_plan_start_date_on_monday():
    assert plan_start_date(date(2026, 6, 8)) == date(2026, 6, 8)


def test_plan_start_date_on_wednesday():
    assert plan_start_date(date(2026, 6, 10)) == date(2026, 6, 15)


def test_workout_date_week1_monday():
    start = date(2026, 6, 15)
    assert workout_date(start, 1, 0) == date(2026, 6, 15)


def test_workout_date_week2_wednesday():
    start = date(2026, 6, 15)
    assert workout_date(start, 2, 2) == date(2026, 6, 24)


def test_assign_dates_sets_scheduled_date():
    week = PlannedWeek(
        week_number=1,
        phase=PhaseName.PREP,
        target_hours=9.0,
        workouts=[
            Workout(
                id="w1",
                sport=Sport.RUN,
                title="Easy run",
                day_of_week=2,
                purpose_tag=PurposeTag.AEROBIC_BASE,
                status=WorkoutStatus.PLANNED,
            )
        ],
    )
    start = date(2026, 6, 15)
    assign_dates(week, start)
    assert week.workouts[0].scheduled_date == date(2026, 6, 17)
