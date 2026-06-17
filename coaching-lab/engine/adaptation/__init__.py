"""Adaptation engine package — Playbook-driven decisions and mutations."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from engine.adaptation.apply import apply_mutations_to_plan
from engine.adaptation.conformance import validate_playbook_conformance
from engine.adaptation.decide import decide
from engine.adaptation.guardrails import validate_mutations_against_guardrails
from engine.adaptation.llm_propose import propose_adaptation
from engine.adaptation.loader import load_playbook
from engine.adaptation.mutate import build_mutations
from engine.adaptation.signals import aggregate_signals
from engine.adaptation.targets import (
    infer_reviewed_week_number,
    resolve_mutation_target_week,
    week_by_number,
)
from engine.adaptation.trajectory import compute_plan_state_delta
from engine.adaptation.weekly_merge import merge_weekly_context
from engine.models import (
    AdaptationDecision,
    AdaptationResult,
    AthleteProfile,
    ConformanceStatus,
    LlmAdaptationProposal,
    PhaseName,
    PlanState,
    TrainingPlan,
    WeeklyContext,
    WorkoutCompletion,
)
from engine.weekly_context import llm_available

# Re-export guardrail constants for backward compatibility.
MAX_WEEKLY_INCREASE = 0.10
MAX_DELOAD_REDUCTION = 0.50


def _build_changes(decision: AdaptationDecision, mutations: list) -> list[str]:
    changes: list[str] = []
    for m in mutations:
        if m.op.value == "scale_week_volume" and m.factor:
            pct = int(abs(1 - m.factor) * 100)
            if m.factor > 1:
                changes.append(f"Increase weekly load up to {pct}%")
            else:
                changes.append(f"Cut weekly load ~{pct}%")
        elif m.op.value == "scale_non_key_duration":
            changes.append("Trim optional volume 10-20%; preserve key sessions")
        elif m.op.value == "remove_optional_session":
            changes.append("Remove optional session")
        elif m.op.value == "strip_intensity_tags":
            changes.append("Remove intensity; keep easy movement")
        elif m.op.value == "replace_workout":
            changes.append("Replace one run with low-impact bike endurance")
        elif m.op.value == "modify_fueling_notes":
            changes.append("Step carbohydrate targets gradually; simplify fueling mix")
        elif m.op.value == "set_gut_training_mode":
            changes.append("Enable gut training mode")
        elif m.op.value == "freeze_progression_rate":
            changes.append("Freeze progression rate")
        elif m.op.value == "pull_deload_forward":
            changes.append("Pull recovery week forward")
    if not changes:
        if decision == AdaptationDecision.HOLD:
            changes.append("Keep load stable and gather more feedback")
        elif decision == AdaptationDecision.PROGRESS:
            changes.append(f"Increase weekly load up to {int(MAX_WEEKLY_INCREASE * 100)}%")
    return changes


def _build_rationale(
    decision: AdaptationDecision,
    signals_msgs: list[str],
    rationale_key: str,
    templates: dict[str, str],
) -> str:
    defaults = {
        AdaptationDecision.PROGRESS: "Consistent, good-quality training with no red flags — safe to progress.",
        AdaptationDecision.HOLD: "Some warning signs present; holding load steady before progressing again.",
        AdaptationDecision.DELOAD: "Multiple warning signals indicate accumulated fatigue; a deload protects the athlete.",
        AdaptationDecision.BIKE_SUBSTITUTE: "Run-specific stress is rising; protecting durability by shifting load to the bike.",
        AdaptationDecision.GUT_TRAINING: "GI symptoms suggest gut training is needed before pushing carb intake further.",
    }
    template = templates.get(decision.value)
    if template and signals_msgs:
        return template.format(
            signals=", ".join(signals_msgs[:3]),
            pct="8",
            trimmed="optional volume",
            key_sessions="key sessions",
            key_session="key long ride",
            days="3-7",
            area="leg",
            carb="60",
        )
    return defaults.get(decision, "Adaptation applied per playbook.")


def evaluate(
    profile: AthleteProfile,
    completions: list[WorkoutCompletion],
    plan_state: PlanState | None = None,
    plan: TrainingPlan | None = None,
    phase: PhaseName | None = None,
    reviewed_week_number: int | None = None,
    week_number: int | None = None,
    is_deload_week: bool | None = None,
    illness_days_off: int = 0,
    playbook_path: Path | None = None,
    weekly_context: WeeklyContext | None = None,
    llm_proposal: LlmAdaptationProposal | None = None,
) -> AdaptationResult:
    """Decide how to adjust the upcoming week from recent feedback.

    Feedback describes ``reviewed_week_number``; micro-mutations apply to the
    next materialized week (reviewed + 1). Macro trajectory updates use
    ``plan_state_delta``.
    """
    loaded = load_playbook(playbook_path)
    spec = loaded.spec
    state = plan_state or PlanState()

    reviewed = reviewed_week_number or week_number or infer_reviewed_week_number(
        completions, plan
    )
    target = resolve_mutation_target_week(reviewed, plan)
    reviewed_week = week_by_number(plan, reviewed) if plan else None
    target_week = week_by_number(plan, target) if plan and target else None

    signal_phase = phase or (reviewed_week.phase if reviewed_week else PhaseName.BASE)
    signal_is_deload = (
        is_deload_week if is_deload_week is not None else (reviewed_week.is_deload if reviewed_week else False)
    )
    mutate_phase = target_week.phase if target_week else signal_phase
    mutate_is_deload = target_week.is_deload if target_week else signal_is_deload

    base_signals = aggregate_signals(
        profile,
        completions,
        spec,
        plan_state=state,
        phase=signal_phase,
        is_deload_week=signal_is_deload,
        illness_days_off=illness_days_off,
    )

    proposal = llm_proposal
    if weekly_context and proposal is None and llm_available():
        proposal = propose_adaptation(
            profile, completions, base_signals, weekly_context, loaded
        )

    merged_context = merge_weekly_context(
        weekly_context,
        proposal.signal_augmentations if proposal else None,
    )

    signals = aggregate_signals(
        profile,
        completions,
        spec,
        plan_state=state,
        phase=signal_phase,
        is_deload_week=signal_is_deload,
        illness_days_off=illness_days_off,
        weekly_context=merged_context,
    )

    decision, rationale_key = decide(
        profile, signals, spec, plan_state=state, phase=signal_phase, is_deload_week=signal_is_deload
    )
    canonical_decision = decision

    conformance = validate_playbook_conformance(proposal, canonical_decision)
    playbook_rule_cited: str | None = None
    llm_proposed_decision = proposal.decision if proposal else None

    insufficient = rationale_key == "insufficient_data"
    mutations = build_mutations(
        decision,
        profile,
        signals,
        spec,
        plan_state=state,
        phase=mutate_phase,
        rationale_key=rationale_key,
        is_deload_week=mutate_is_deload,
    )

    state_delta = compute_plan_state_delta(
        decision, state, spec, week_number=reviewed
    )

    for m in mutations:
        if m.op.value == "set_run_volume_cap" and m.value is not None:
            state_delta["run_volume_cap"] = m.value
        if m.op.value == "set_gut_training_mode":
            state_delta["gut_training_mode"] = True
            state_delta["gut_carb_floor"] = spec.gut_training.carb_floor_default

    diff = None
    if plan and mutations and target is not None:
        prior_week = reviewed_week or week_by_number(plan, reviewed)
        prior_hours = prior_week.target_hours if prior_week else 0.0
        preview_plan, diff = apply_mutations_to_plan(plan, mutations, target)
        target_after = week_by_number(preview_plan, target)
        new_hours = target_after.target_hours if target_after else prior_hours
        guard_violations = validate_mutations_against_guardrails(
            mutations, spec, prior_hours, new_hours
        )
        if guard_violations:
            decision = AdaptationDecision.HOLD
            rationale_key = "guardrail_fallback"
            mutations = build_mutations(
                decision,
                profile,
                signals,
                spec,
                plan_state=state,
                phase=mutate_phase,
                is_deload_week=mutate_is_deload,
            )
            preview_plan, diff = apply_mutations_to_plan(plan, mutations, target)
            signals_msgs = signals.flag_messages + guard_violations
        else:
            signals_msgs = signals.flag_messages
    else:
        signals_msgs = signals.flag_messages

    if decision == AdaptationDecision.BIKE_SUBSTITUTE and "Run orthopedic stress detected" not in signals_msgs:
        signals_msgs = signals_msgs + ["Run orthopedic stress detected"]
    if decision == AdaptationDecision.GUT_TRAINING and "Fueling intolerance in sessions" not in signals_msgs:
        signals_msgs = signals_msgs + ["Fueling intolerance in sessions"]

    if conformance.status == ConformanceStatus.MATCHED and conformance.accepted_rationale:
        rationale = conformance.accepted_rationale
        playbook_rule_cited = conformance.playbook_rule_cited
    else:
        rationale = _build_rationale(
            decision, signals_msgs, rationale_key, spec.narrator_templates
        )

    weekly_summary = merged_context.summary if merged_context else None

    return AdaptationResult(
        decision=decision,
        signals=signals_msgs,
        changes=_build_changes(decision, mutations),
        rationale=rationale,
        mutations=mutations,
        plan_state_delta=state_delta,
        playbook_version=loaded.checksum,
        diff=diff,
        insufficient_data=insufficient,
        reviewed_week_number=reviewed,
        target_week_number=target,
        weekly_context_summary=weekly_summary,
        conformance_status=conformance.status,
        playbook_rule_cited=playbook_rule_cited,
        canonical_decision=canonical_decision,
        llm_proposed_decision=llm_proposed_decision,
    )


__all__ = [
    "evaluate",
    "load_playbook",
    "MAX_WEEKLY_INCREASE",
    "MAX_DELOAD_REDUCTION",
]
