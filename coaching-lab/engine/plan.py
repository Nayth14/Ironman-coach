"""Plan generation: orchestrates periodization, strength, scheduling, and LLM enrichment."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date

from engine import calendar, enrich, periodization, scheduler, strength
from engine.models import AthleteProfile, Phase, PlanState, TrainingPlan
from engine.readiness import weeks_to_race
from engine.rules.validate import assert_plan_valid
from engine.workout_bank.assign import assign_bank_workouts


def _week_in_phase_ratio(week_number: int, phase: Phase) -> float:
    span = max(1, phase.end_week - phase.start_week)
    return (week_number - phase.start_week) / span


def iter_generate_plan(
    profile: AthleteProfile,
    today: date | None = None,
    max_weeks_to_build: int = 4,
    plan_state: "PlanState | None" = None,
) -> Iterator[str | TrainingPlan]:
    """Generate a plan, yielding progress messages then the final TrainingPlan."""
    ref_today = today or date.today()
    total_weeks = weeks_to_race(profile.race_date, ref_today)
    total_weeks = max(4, total_weeks)

    yield "Scheduling your macrocycle…"
    start = calendar.plan_start_date(ref_today)
    phases = periodization.build_phases(profile, total_weeks)
    state = plan_state or PlanState()

    weeks = []
    build_count = min(max_weeks_to_build, total_weeks)
    for week_number in range(1, build_count + 1):
        yield f"Building week {week_number} of {build_count}…"
        phase_name = periodization.phase_for_week(phases, week_number)
        phase = next(p for p in phases if p.name == phase_name)
        is_deload = periodization.is_deload_week(week_number, phase_name)
        if week_number in state.forced_deload_weeks:
            is_deload = True
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
        if state.volume_multiplier != 1.0:
            week.target_hours *= state.volume_multiplier
        if state.run_volume_cap < 1.0:
            for w in week.workouts:
                if w.sport.value == "run" and w.estimated_duration_seconds:
                    w.estimated_duration_seconds = int(
                        w.estimated_duration_seconds * state.run_volume_cap
                    )
        week = assign_bank_workouts(week, phase=phase_name, state=state)
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
    yield plan


def generate_plan(
    profile: AthleteProfile,
    today: date | None = None,
    max_weeks_to_build: int = 4,
    plan_state: "PlanState | None" = None,
) -> TrainingPlan:
    """Generate the macrocycle and materialize the first N weeks of workouts.

    Deterministic scheduling sets volume and placement; LLM fills workout steps.
    """
    plan: TrainingPlan | None = None
    for item in iter_generate_plan(profile, today, max_weeks_to_build, plan_state):
        if isinstance(item, TrainingPlan):
            plan = item
    assert plan is not None
    return plan
