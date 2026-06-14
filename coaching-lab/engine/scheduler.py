"""Build the weekly training calendar.

Delegates to ``engine.rules.placement`` so every week satisfies the hard
Ironman ruleset, then validates before returning.
"""

from __future__ import annotations

from engine.models import (
    AthleteProfile,
    PlannedWeek,
    StrengthExercise,
    StrengthPlan,
)
from engine.rules.placement import schedule_week
from engine.rules.validate import RuleContext, assert_plan_valid, validate_week

# Re-export for callers/tests that referenced scheduler constants.
from engine.rules.semantics import DELOAD_VOLUME_FACTOR as _DELOAD_FACTOR  # noqa: F401
from engine.rules.semantics import DISCIPLINE_SPLIT as _DISCIPLINE_SPLIT  # noqa: F401


def build_week(
    week_number: int,
    phase,
    is_deload: bool,
    profile: AthleteProfile,
    strength_plan: StrengthPlan,
    strength_exercises: list[StrengthExercise],
    week_in_phase_ratio: float = 0.5,
    total_weeks: int = 24,
) -> PlannedWeek:
    week = schedule_week(
        week_number=week_number,
        phase=phase,
        is_deload=is_deload,
        profile=profile,
        strength_plan=strength_plan,
        strength_exercises=strength_exercises,
        week_in_phase_ratio=week_in_phase_ratio,
        total_weeks=total_weeks,
    )
    ctx = RuleContext(race_date=profile.race_date, total_weeks=total_weeks)
    violations = validate_week(week, ctx)
    if violations:
        from engine.rules.validate import RulesetViolationError

        raise RulesetViolationError(violations)
    return week
