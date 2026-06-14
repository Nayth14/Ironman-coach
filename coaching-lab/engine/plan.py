"""Plan generation: orchestrates periodization, strength, scheduling, and LLM enrichment."""

from __future__ import annotations

from datetime import date

from engine import calendar, enrich, periodization, scheduler, strength
from engine.models import AthleteProfile, Phase, TrainingPlan
from engine.readiness import weeks_to_race
from engine.rules.validate import assert_plan_valid


def _week_in_phase_ratio(week_number: int, phase: Phase) -> float:
    span = max(1, phase.end_week - phase.start_week)
    return (week_number - phase.start_week) / span


def generate_plan(
    profile: AthleteProfile,
    today: date | None = None,
    max_weeks_to_build: int = 4,
) -> TrainingPlan:
    """Generate the macrocycle and materialize the first N weeks of workouts.

    Deterministic scheduling sets volume and placement; LLM fills workout steps.
    """
    ref_today = today or date.today()
    total_weeks = weeks_to_race(profile.race_date, ref_today)
    total_weeks = max(4, total_weeks)

    start = calendar.plan_start_date(ref_today)
    phases = periodization.build_phases(profile, total_weeks)

    weeks = []
    build_count = min(max_weeks_to_build, total_weeks)
    for week_number in range(1, build_count + 1):
        phase_name = periodization.phase_for_week(phases, week_number)
        phase = next(p for p in phases if p.name == phase_name)
        is_deload = periodization.is_deload_week(week_number, phase_name)
        ratio = _week_in_phase_ratio(week_number, phase)

        strength_plan = strength.prescribe_for_week(profile, phase_name, is_deload)
        strength_exercises = strength.select_exercises(profile, phase_name)

        week = scheduler.build_week(
            week_number=week_number,
            phase=phase_name,
            is_deload=is_deload,
            profile=profile,
            strength_plan=strength_plan,
            strength_exercises=strength_exercises,
            week_in_phase_ratio=ratio,
            total_weeks=total_weeks,
        )
        calendar.assign_dates(week, start)
        week = enrich.enrich_week_steps(week, profile, phase_name)
        week.strength_plan = strength_plan
        weeks.append(week)

    plan = TrainingPlan(
        athlete_race_date=profile.race_date,
        total_weeks=total_weeks,
        plan_start_date=start,
        phases=phases,
        strength_plan=weeks[0].strength_plan or strength.prescribe(profile, phases[0].name),
        weeks=weeks,
    )
    assert_plan_valid(plan)
    return plan
