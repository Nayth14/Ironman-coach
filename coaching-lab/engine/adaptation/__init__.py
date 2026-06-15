"""Adaptation engine package — Playbook-driven decisions and mutations."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from engine.adaptation.apply import apply_mutations_to_plan
from engine.adaptation.decide import decide
from engine.adaptation.guardrails import validate_mutations_against_guardrails
from engine.adaptation.loader import load_playbook
from engine.adaptation.mutate import build_mutations
from engine.adaptation.signals import aggregate_signals
from engine.adaptation.trajectory import compute_plan_state_delta
from engine.models import (
    AdaptationDecision,
    AdaptationResult,
    AthleteProfile,
    PhaseName,
    PlanState,
    TrainingPlan,
    WorkoutCompletion,
)

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
    phase: PhaseName = PhaseName.BASE,
    week_number: int = 1,
    is_deload_week: bool = False,
    illness_days_off: int = 0,
    playbook_path: Path | None = None,
) -> AdaptationResult:
    """Decide how to adjust the upcoming week from recent feedback."""
    loaded = load_playbook(playbook_path)
    spec = loaded.spec
    state = plan_state or PlanState()

    signals = aggregate_signals(
        profile,
        completions,
        spec,
        plan_state=state,
        phase=phase,
        is_deload_week=is_deload_week,
        illness_days_off=illness_days_off,
    )

    decision, rationale_key = decide(
        profile, signals, spec, plan_state=state, phase=phase, is_deload_week=is_deload_week
    )

    insufficient = rationale_key == "insufficient_data"
    mutations = build_mutations(
        decision,
        profile,
        signals,
        spec,
        plan_state=state,
        phase=phase,
        rationale_key=rationale_key,
        is_deload_week=is_deload_week,
    )

    state_delta = compute_plan_state_delta(decision, state, spec, week_number=week_number)

    for m in mutations:
        if m.op.value == "set_run_volume_cap" and m.value is not None:
            state_delta["run_volume_cap"] = m.value
        if m.op.value == "set_gut_training_mode":
            state_delta["gut_training_mode"] = True
            state_delta["gut_carb_floor"] = spec.gut_training.carb_floor_default

    diff = None
    if plan and plan.weeks and mutations:
        prior_hours = plan.weeks[0].target_hours
        preview_plan, diff = apply_mutations_to_plan(plan, mutations, week_number)
        new_hours = preview_plan.weeks[0].target_hours if preview_plan.weeks else prior_hours
        guard_violations = validate_mutations_against_guardrails(
            mutations, spec, prior_hours, new_hours
        )
        if guard_violations:
            decision = AdaptationDecision.HOLD
            rationale_key = "guardrail_fallback"
            mutations = build_mutations(
                decision, profile, signals, spec, plan_state=state, phase=phase
            )
            preview_plan, diff = apply_mutations_to_plan(plan, mutations, week_number)
            signals_msgs = signals.flag_messages + guard_violations
        else:
            signals_msgs = signals.flag_messages
    else:
        signals_msgs = signals.flag_messages

    if decision == AdaptationDecision.BIKE_SUBSTITUTE and "Run orthopedic stress detected" not in signals_msgs:
        signals_msgs = signals_msgs + ["Run orthopedic stress detected"]
    if decision == AdaptationDecision.GUT_TRAINING and "Fueling intolerance in sessions" not in signals_msgs:
        signals_msgs = signals_msgs + ["Fueling intolerance in sessions"]

    return AdaptationResult(
        decision=decision,
        signals=signals_msgs,
        changes=_build_changes(decision, mutations),
        rationale=_build_rationale(decision, signals_msgs, rationale_key, spec.narrator_templates),
        mutations=mutations,
        plan_state_delta=state_delta,
        playbook_version=loaded.checksum,
        diff=diff,
        insufficient_data=insufficient,
    )


__all__ = [
    "evaluate",
    "load_playbook",
    "MAX_WEEKLY_INCREASE",
    "MAX_DELOAD_REDUCTION",
]
