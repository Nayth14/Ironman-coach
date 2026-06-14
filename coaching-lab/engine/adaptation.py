"""Adaptation engine: progress / hold / deload decisions from feedback.

Encodes the adaptation rules from the coaching framework. Deterministic — the
LLM only narrates the result afterward. Hard guardrails live here.
"""

from __future__ import annotations

from engine.models import (
    AdaptationDecision,
    AdaptationResult,
    AthleteProfile,
    Sport,
    WorkoutCompletion,
)

# Guardrails (hard limits, never exceeded regardless of signals).
MAX_WEEKLY_INCREASE = 0.10
MAX_DELOAD_REDUCTION = 0.50

# Thresholds
_HIGH_RPE = 8
_LOW_READINESS = 4


def _count_warning_flags(completions: list[WorkoutCompletion]) -> tuple[int, list[str]]:
    flags: list[str] = []

    if not completions:
        return 0, flags

    high_rpe = [c for c in completions if c.rpe is not None and c.rpe >= _HIGH_RPE]
    if len(high_rpe) >= 2:
        flags.append(f"Elevated RPE on {len(high_rpe)} sessions")

    low_readiness = [
        c for c in completions
        if c.readiness_score is not None and c.readiness_score <= _LOW_READINESS
    ]
    if len(low_readiness) >= 2:
        flags.append(f"Low readiness reported {len(low_readiness)}x")

    all_fatigue = [f for c in completions for f in c.fatigue_flags]
    if all_fatigue:
        flags.append(f"Fatigue flags: {', '.join(sorted(set(all_fatigue)))}")

    key_missed = [
        c for c in completions if not c.completed
    ]
    if key_missed:
        flags.append(f"{len(key_missed)} missed session(s)")

    return len(flags), flags


def _run_orthopedic_stress(
    profile: AthleteProfile, completions: list[WorkoutCompletion]
) -> bool:
    """Detect rising run-specific orthopedic stress."""
    run_complaints = []
    injury_areas = {f.lower() for f in profile.injury_flags}
    for c in completions:
        if c.sport != Sport.RUN:
            continue
        for f in c.fatigue_flags:
            low = f.lower()
            if any(area in low for area in ["knee", "shin", "calf", "achilles", "foot", "hip"]):
                run_complaints.append(f)
            if injury_areas and any(area in low for area in injury_areas):
                run_complaints.append(f)
    return len(run_complaints) >= 1


def _fueling_intolerance(completions: list[WorkoutCompletion]) -> bool:
    for c in completions:
        for f in c.fatigue_flags:
            low = f.lower()
            if any(k in low for k in ["gi", "stomach", "gut", "nausea", "cramp"]):
                return True
    return False


def evaluate(
    profile: AthleteProfile,
    completions: list[WorkoutCompletion],
) -> AdaptationResult:
    """Decide how to adjust the upcoming week from recent feedback."""
    flag_count, flags = _count_warning_flags(completions)

    # Specialized routes first.
    if _run_orthopedic_stress(profile, completions):
        return AdaptationResult(
            decision=AdaptationDecision.BIKE_SUBSTITUTE,
            signals=flags + ["Run orthopedic stress detected"],
            changes=[
                "Lower run intensity and volume",
                "Replace one run with low-impact bike endurance",
                "Protect run frequency but reduce load",
            ],
            rationale="Run-specific stress is rising; protecting durability by shifting load to the bike.",
        )

    if _fueling_intolerance(completions):
        return AdaptationResult(
            decision=AdaptationDecision.GUT_TRAINING,
            signals=flags + ["Fueling intolerance in sessions"],
            changes=[
                "Step carbohydrate targets gradually",
                "Simplify fueling product mix",
                "Rehearse fueling in long sessions",
            ],
            rationale="GI symptoms suggest gut training is needed before pushing carb intake further.",
        )

    # General progress/hold/deload ladder.
    completed = [c for c in completions if c.completed]
    key_quality_ok = all(
        (c.rpe is None or c.rpe < _HIGH_RPE) for c in completed
    )

    if flag_count >= 3:
        return AdaptationResult(
            decision=AdaptationDecision.DELOAD,
            signals=flags,
            changes=[
                f"Cut weekly load up to {int(MAX_DELOAD_REDUCTION * 100)}% for 3-7 days",
                "Remove intensity; keep easy movement",
                "Restore sleep and fueling before rebuilding",
            ],
            rationale="Multiple warning signals indicate accumulated fatigue; a deload protects the athlete.",
        )

    if flag_count >= 1:
        return AdaptationResult(
            decision=AdaptationDecision.HOLD,
            signals=flags,
            changes=[
                "Keep load stable this week",
                "Preserve key sessions; trim optional volume 10-20%",
            ],
            rationale="Some warning signs present; holding load steady before progressing again.",
        )

    if completed and key_quality_ok:
        return AdaptationResult(
            decision=AdaptationDecision.PROGRESS,
            signals=["Key sessions completed at target quality", "No warning flags"],
            changes=[
                f"Increase weekly load up to {int(MAX_WEEKLY_INCREASE * 100)}%",
                "Or increase key-session density",
            ],
            rationale="Consistent, good-quality training with no red flags — safe to progress.",
        )

    return AdaptationResult(
        decision=AdaptationDecision.HOLD,
        signals=["Insufficient data to progress"],
        changes=["Keep load stable and gather more feedback"],
        rationale="Not enough completed sessions yet to justify a load increase.",
    )
