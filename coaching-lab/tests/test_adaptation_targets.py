"""Tests for reviewed-week vs target-week adaptation targeting."""

from __future__ import annotations

from datetime import date

from engine import adaptation
from engine.adaptation.apply import apply_mutations_to_plan
from engine.adaptation.targets import (
    infer_reviewed_week_number,
    resolve_mutation_target_week,
)
from engine.fixtures import load_fixture
from engine.models import AdaptationDecision, PlanState, PurposeTag, WeeklyContext, WorkoutCompletion
from engine.plan import generate_plan


def _is_optional(w) -> bool:
    return not w.is_key_session and w.purpose_tag in (
        PurposeTag.AEROBIC_BASE,
        PurposeTag.ECONOMY,
        PurposeTag.RECOVERY,
    )


def _week_completions(week) -> list[WorkoutCompletion]:
    return [
        WorkoutCompletion(
            workout_id=w.id,
            sport=w.sport,
            completed=True,
            rpe=5,
            is_key_session=w.is_key_session,
            is_optional=_is_optional(w),
            week_number=week.week_number,
        )
        for w in week.workouts
    ]


def test_resolve_mutation_target_week_requires_materialized_next_week():
    _, profile = load_fixture("beginner_first_im")
    plan = generate_plan(profile, today=date(2026, 3, 1))

    assert resolve_mutation_target_week(1, plan) == 2
    assert resolve_mutation_target_week(plan.total_weeks, plan) is None


def test_infer_reviewed_week_from_completion_week_numbers():
    _, profile = load_fixture("beginner_first_im")
    plan = generate_plan(profile, today=date(2026, 3, 1))
    completions = _week_completions(plan.weeks[0])

    assert infer_reviewed_week_number(completions, plan) == 1


def test_progress_mutates_week_2_not_week_1():
    _, profile = load_fixture("beginner_first_im")
    plan = generate_plan(profile, today=date(2026, 3, 1))
    week1 = plan.weeks[0]
    week2_before_hours = plan.weeks[1].target_hours
    week1_before_hours = week1.target_hours

    result = adaptation.evaluate(
        profile,
        _week_completions(week1),
        plan_state=PlanState(),
        plan=plan,
        reviewed_week_number=1,
    )

    assert result.reviewed_week_number == 1
    assert result.target_week_number == 2
    assert result.decision.value == "progress"
    assert result.diff is not None

    updated, _ = apply_mutations_to_plan(plan, result.mutations, result.target_week_number)
    assert updated.weeks[0].target_hours == week1_before_hours
    assert updated.weeks[1].target_hours != week2_before_hours
    assert updated.weeks[1].target_hours > week2_before_hours


def test_evaluate_with_weekly_context_changes_decision():
    _, profile = load_fixture("beginner_first_im")
    plan = generate_plan(profile, today=date(2026, 3, 1))
    week1 = plan.weeks[0]
    completions = _week_completions(week1)

    baseline = adaptation.evaluate(
        profile,
        completions,
        plan_state=PlanState(),
        plan=plan,
        reviewed_week_number=1,
    )

    ctx = WeeklyContext(
        life_stress=True,
        fatigue_flags=["poor sleep"],
        summary="Rough travel week with poor sleep",
    )
    with_context = adaptation.evaluate(
        profile,
        completions,
        plan_state=PlanState(),
        plan=plan,
        reviewed_week_number=1,
        weekly_context=ctx,
    )

    assert with_context.weekly_context_summary == ctx.summary
    assert with_context.conformance_status is not None
    if baseline.decision == AdaptationDecision.PROGRESS:
        assert with_context.decision != AdaptationDecision.PROGRESS
