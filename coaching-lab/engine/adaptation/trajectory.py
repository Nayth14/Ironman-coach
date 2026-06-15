"""Macro trajectory updates from adaptation decisions."""

from __future__ import annotations

from engine.adaptation.spec import PlaybookSpec
from engine.models import AdaptationDecision, PlanState, ProgressionRate


def _drop_progression(rate: ProgressionRate) -> ProgressionRate:
    if rate == ProgressionRate.NORMAL:
        return ProgressionRate.SLOW
    return ProgressionRate.FROZEN


def _recover_progression(rate: ProgressionRate) -> ProgressionRate:
    if rate == ProgressionRate.FROZEN:
        return ProgressionRate.SLOW
    return ProgressionRate.NORMAL


def compute_plan_state_delta(
    decision: AdaptationDecision,
    current: PlanState,
    spec: PlaybookSpec,
    week_number: int | None = None,
) -> dict[str, object]:
    """Return delta to merge into PlanState after a decision."""
    delta: dict[str, object] = {}
    mr = spec.macro_rules

    if decision == AdaptationDecision.PROGRESS:
        delta["consecutive_holds"] = 0
        delta["consecutive_deloads"] = 0
        if current.progression_rate != ProgressionRate.NORMAL:
            delta["progression_rate"] = _recover_progression(current.progression_rate).value
        delta["progression_frozen_weeks"] = 0
        delta["volume_multiplier"] = min(
            current.volume_multiplier * 1.05,
            1.0 + spec.guardrails.max_weekly_increase,
        )

    elif decision == AdaptationDecision.HOLD:
        delta["consecutive_holds"] = current.consecutive_holds + 1
        delta["progression_rate"] = _drop_progression(current.progression_rate).value
        delta["progression_frozen_weeks"] = max(current.progression_frozen_weeks, 1)

    elif decision == AdaptationDecision.DELOAD:
        delta["consecutive_holds"] = 0
        delta["consecutive_deloads"] = current.consecutive_deloads + 1
        delta["weeks_since_recovery"] = 0
        delta["progression_rate"] = ProgressionRate.FROZEN.value
        delta["progression_frozen_weeks"] = mr.consecutive_holds_pull_deload + 1
        if current.consecutive_holds >= spec.thresholds.consecutive_holds_escalate - 1:
            forced = list(current.forced_deload_weeks)
            if week_number is not None:
                forced.append(week_number + 1)
            delta["forced_deload_weeks"] = forced

    elif decision == AdaptationDecision.BIKE_SUBSTITUTE:
        delta["consecutive_holds"] = current.consecutive_holds + 1

    elif decision == AdaptationDecision.GUT_TRAINING:
        delta["gut_training_mode"] = True

    history = list(current.decision_history)
    history.append(decision.value)
    delta["decision_history"] = history[-20:]

    return delta


def apply_plan_state_delta(state: PlanState, delta: dict[str, object]) -> PlanState:
    data = state.model_dump()
    data.update(delta)
    return PlanState.model_validate(data)
