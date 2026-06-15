"""Hard guardrail floor — Playbook may be more conservative, never less."""

from __future__ import annotations

from engine.adaptation.spec import PlaybookSpec
from engine.models import MutationOp, PlanMutation, PlannedWeek, TrainingPlan
from engine.rules.validate import validate_plan, validate_week


class GuardrailViolation(Exception):
    def __init__(self, messages: list[str]) -> None:
        self.messages = messages
        super().__init__("; ".join(messages))


def validate_mutations_against_guardrails(
    mutations: list[PlanMutation],
    spec: PlaybookSpec,
    prior_hours: float,
    new_hours: float,
) -> list[str]:
    violations: list[str] = []
    g = spec.guardrails

    if prior_hours > 0:
        increase = (new_hours - prior_hours) / prior_hours
        if increase > g.max_weekly_increase + 0.001:
            violations.append(
                f"Volume increase {increase:.1%} exceeds GR-VOL10 ({g.max_weekly_increase:.0%})"
            )
        reduction = (prior_hours - new_hours) / prior_hours
        if reduction > g.max_deload_reduction + 0.001:
            violations.append(
                f"Volume reduction {reduction:.1%} exceeds GR-DEL50 ({g.max_deload_reduction:.0%})"
            )

    has_volume_up = any(
        m.op == MutationOp.SCALE_WEEK_VOLUME and m.factor is not None and m.factor > 1.0
        for m in mutations
    )
    has_density = any(m.op == MutationOp.ADVANCE_PROGRESSION_RATE for m in mutations)
    if has_volume_up and has_density:
        violations.append("Volume and density increase in same week forbidden")

    return violations


def assert_plan_still_valid(plan: TrainingPlan) -> None:
    violations = validate_plan(plan)
    if violations:
        raise GuardrailViolation([f"{v.rule_id}: {v.message}" for v in violations])
