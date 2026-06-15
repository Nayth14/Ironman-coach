"""Build mutation operations from decision + Playbook."""

from __future__ import annotations

from engine.adaptation.signals import SignalSummary
from engine.adaptation.spec import PlaybookSpec
from engine.models import (
    AdaptationDecision,
    AthleteProfile,
    ExperienceLevel,
    MutationOp,
    PhaseName,
    PlanMutation,
    PlanState,
    Sport,
)


def _experience_cap(profile: AthleteProfile, spec: PlaybookSpec) -> float:
    return spec.experience_progress_caps.get(
        profile.experience_level.value,
        spec.experience_progress_caps.get("intermediate", 0.08),
    )


def _hold_trim(profile: AthleteProfile, signals: SignalSummary, spec: PlaybookSpec) -> float:
    if signals.flag_count <= 1:
        base = spec.hold_trim_single_flag
    else:
        base = spec.hold_trim_multi_flag
    exp_trim = spec.experience_hold_trim.get(profile.experience_level.value)
    if exp_trim is not None:
        return max(base, exp_trim)
    return base


def _run_cap(profile: AthleteProfile, spec: PlaybookSpec, chronic: bool) -> float | None:
    if not chronic:
        return None
    return spec.run_volume_cap.model_dump().get(profile.experience_level.value, 0.7)


def build_mutations(
    decision: AdaptationDecision,
    profile: AthleteProfile,
    signals: SignalSummary,
    spec: PlaybookSpec,
    plan_state: PlanState | None = None,
    phase: PhaseName = PhaseName.BASE,
    rationale_key: str = "",
    is_deload_week: bool = False,
) -> list[PlanMutation]:
    state = plan_state or PlanState()
    mutations: list[PlanMutation] = []

    if decision == AdaptationDecision.PROGRESS:
        cap = _experience_cap(profile, spec)
        phase_factor = spec.phase_progress_factors.get(phase.value, 1.0)
        factor = min(1.0 + cap * phase_factor, 1.0 + spec.guardrails.max_weekly_increase)
        if phase == PhaseName.BUILD and phase_factor < 1.0:
            mutations.append(PlanMutation(op=MutationOp.ADVANCE_PROGRESSION_RATE))
        else:
            mutations.append(PlanMutation(op=MutationOp.SCALE_WEEK_VOLUME, factor=factor))
            mutations.append(PlanMutation(op=MutationOp.ADD_EASY_AEROBIC))

    elif decision == AdaptationDecision.HOLD:
        trim = 1.0 - _hold_trim(profile, signals, spec)
        mutations.append(PlanMutation(op=MutationOp.SCALE_NON_KEY_DURATION, factor=trim))
        if signals.flag_count >= 2:
            mutations.append(PlanMutation(op=MutationOp.REMOVE_OPTIONAL_SESSION))
        mutations.append(PlanMutation(op=MutationOp.FREEZE_PROGRESSION_RATE, weeks=1))

    elif decision == AdaptationDecision.DELOAD:
        if is_deload_week:
            factor = 1.0 - spec.guardrails.default_deload_factor
        elif signals.weighted_flags >= 4:
            factor = 1.0 - spec.guardrails.max_deload_reduction
        else:
            factor = 1.0 - spec.guardrails.default_deload_factor
        factor = max(factor, 1.0 - spec.guardrails.max_deload_reduction)
        mutations.append(PlanMutation(op=MutationOp.SCALE_WEEK_VOLUME, factor=factor))
        mutations.append(PlanMutation(op=MutationOp.STRIP_INTENSITY_TAGS))
        if rationale_key == "consecutive_holds_escalate" or rationale_key == "stacked_flags":
            mutations.append(PlanMutation(op=MutationOp.PULL_DELOAD_FORWARD, weeks=1))
            mutations.append(PlanMutation(op=MutationOp.FREEZE_PROGRESSION_RATE, weeks=2))
        if signals.illness_reentry:
            mutations.append(PlanMutation(op=MutationOp.INSERT_RECOVERY_BLOCK, days=7))

    elif decision == AdaptationDecision.BIKE_SUBSTITUTE:
        mutations.append(
            PlanMutation(
                op=MutationOp.REPLACE_WORKOUT,
                target_sport=Sport.RUN,
                notes="bike_endurance",
            )
        )
        chronic = rationale_key == "chronic_orthopedic"
        cap = _run_cap(profile, spec, chronic)
        if cap is not None:
            mutations.append(PlanMutation(op=MutationOp.SET_RUN_VOLUME_CAP, value=cap))

    elif decision == AdaptationDecision.GUT_TRAINING:
        mutations.append(PlanMutation(op=MutationOp.SET_GUT_TRAINING_MODE, bool_value=True))
        mutations.append(
            PlanMutation(
                op=MutationOp.MODIFY_FUELING_NOTES,
                value=float(spec.gut_training.carb_floor_default),
                notes="simplify_product_mix",
            )
        )
        if signals.gi_all_sessions:
            mutations.append(PlanMutation(op=MutationOp.HOLD_GLOBAL_VOLUME))

    return mutations
