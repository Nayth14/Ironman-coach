"""Decision ladder sourced from PlaybookSpec."""

from __future__ import annotations

from engine.adaptation.signals import SignalSummary
from engine.adaptation.spec import PlaybookSpec
from engine.models import (
    AdaptationDecision,
    AthleteProfile,
    ExperienceLevel,
    PhaseName,
    PlanState,
)


def decide(
    profile: AthleteProfile,
    signals: SignalSummary,
    spec: PlaybookSpec,
    plan_state: PlanState | None = None,
    phase: PhaseName = PhaseName.BASE,
    is_deload_week: bool = False,
) -> tuple[AdaptationDecision, str]:
    """Return decision and short rationale key."""
    state = plan_state or PlanState()
    t = spec.thresholds

    if signals.illness_reentry:
        return AdaptationDecision.DELOAD, "illness_reentry"

    if signals.has_orthopedic_stress:
        if signals.orthopedic_session_count >= spec.chronic_orthopedic_min_sessions:
            return AdaptationDecision.BIKE_SUBSTITUTE, "chronic_orthopedic"
        return AdaptationDecision.BIKE_SUBSTITUTE, "niggle_orthopedic"

    if signals.has_gi_stress:
        return AdaptationDecision.GUT_TRAINING, "gi_systemic" if signals.gi_all_sessions else "gi_scoped"

    effective_flags = max(signals.flag_count, int(signals.weighted_flags))

    if state.consecutive_holds >= t.consecutive_holds_escalate - 1 and effective_flags >= 1:
        return AdaptationDecision.DELOAD, "consecutive_holds_escalate"

    if effective_flags >= t.deload_flag_count:
        return AdaptationDecision.DELOAD, "stacked_flags"

    if effective_flags >= t.hold_flag_count_min:
        return AdaptationDecision.HOLD, "warning_flags"

    if signals.insufficient_data:
        return AdaptationDecision.HOLD, "insufficient_data"

    if signals.partial_week and effective_flags == 0:
        # Partial week with clean signals: allow progress if minimum met
        pass
    elif signals.partial_week:
        return AdaptationDecision.HOLD, "partial_week"

    if profile.injury_flags:
        return AdaptationDecision.HOLD, "injury_flags_present"

    if phase == PhaseName.TAPER:
        return AdaptationDecision.HOLD, "taper_no_progress"

    if (
        signals.all_completed
        and signals.all_rpe_below_high
        and signals.completed_count >= t.min_completed_sessions
        and signals.key_completed_count >= t.min_key_completed_sessions
        and not signals.prior_week_had_flags
        and state.progression_frozen_weeks <= 0
    ):
        return AdaptationDecision.PROGRESS, "all_green"

    return AdaptationDecision.HOLD, "default_hold"
