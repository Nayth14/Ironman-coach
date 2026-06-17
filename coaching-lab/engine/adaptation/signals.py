"""Aggregate athlete feedback signals across time windows."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

from engine.adaptation.spec import PlaybookSpec
from engine.models import (
    AthleteProfile,
    PhaseName,
    PlanState,
    Sport,
    WeeklyContext,
    WorkoutCompletion,
)


@dataclass
class SignalSummary:
    flag_count: int
    flag_messages: list[str]
    weighted_flags: float
    completed_count: int
    key_completed_count: int
    missed_key_count: int
    high_rpe_sessions: int
    low_readiness_sessions: int
    has_orthopedic_stress: bool
    orthopedic_session_count: int
    has_gi_stress: bool
    gi_session_count: int
    gi_all_sessions: bool
    all_rpe_below_high: bool
    all_completed: bool
    insufficient_data: bool
    partial_week: bool
    illness_reentry: bool
    prior_week_had_flags: bool = False


def _window_completions(
    completions: list[WorkoutCompletion],
    days: int,
    ref_date: date | None = None,
) -> list[WorkoutCompletion]:
    if not completions:
        return []
    ref = ref_date or date.today()
    cutoff = ref - timedelta(days=days)
    out = []
    for c in completions:
        if c.completed_at is None or c.completed_at >= cutoff:
            out.append(c)
    return out if any(c.completed_at for c in completions) else completions


def _matches_keywords(text: str, keywords: list[str]) -> bool:
    low = text.lower()
    return any(k in low for k in keywords)


def _weekly_fatigue_flags(weekly_context: WeeklyContext | None) -> list[str]:
    if not weekly_context:
        return []
    return list(weekly_context.fatigue_flags)


def aggregate_signals(
    profile: AthleteProfile,
    completions: list[WorkoutCompletion],
    spec: PlaybookSpec,
    plan_state: PlanState | None = None,
    phase: PhaseName = PhaseName.BASE,
    is_deload_week: bool = False,
    illness_days_off: int = 0,
    ref_date: date | None = None,
    weekly_context: WeeklyContext | None = None,
) -> SignalSummary:
    """Aggregate signals for the 7-day decision window with 14-day gating."""
    if weekly_context and weekly_context.illness_days_off:
        illness_days_off = max(illness_days_off, weekly_context.illness_days_off)

    t = spec.thresholds
    w7 = _window_completions(completions, spec.windows.decision_days, ref_date)
    w14_prior = _window_completions(completions, spec.windows.trend_days, ref_date)
    # Prior 7 days within 14-day window (days 8-14 ago approximation)
    prior_flags = False

    flags: list[str] = []
    weighted = 0.0

    high_rpe = [c for c in w7 if c.rpe is not None and c.rpe >= spec.thresholds.high_rpe]
    if len(high_rpe) >= t.high_rpe_min_sessions:
        flags.append(f"Elevated RPE on {len(high_rpe)} sessions")
        weighted += 1.0

    low_read = [
        c for c in w7
        if c.readiness_score is not None and c.readiness_score <= spec.thresholds.low_readiness
    ]
    if len(low_read) >= t.low_readiness_min_sessions:
        flags.append(f"Low readiness reported {len(low_read)}x")
        weighted += 1.0

    fatigue_flags = [f for c in w7 for f in c.fatigue_flags]
    fatigue_flags.extend(_weekly_fatigue_flags(weekly_context))
    if fatigue_flags:
        flags.append(f"Fatigue flags: {', '.join(sorted(set(fatigue_flags)))}")
        weighted += 1.0

    if weekly_context and weekly_context.life_stress:
        flags.append("Life stress / poor sleep reported")
        weighted += 1.0

    missed = [c for c in w7 if not c.completed]
    for m in missed:
        if m.is_key_session:
            flags.append("Missed key session")
            weighted += spec.flag_weights.missed_key_session
        elif m.is_optional:
            weighted += spec.flag_weights.missed_optional_session
        else:
            flags.append("Missed session")
            weighted += spec.flag_weights.missed_default_session

    completed = [c for c in w7 if c.completed]
    key_completed = [c for c in completed if c.is_key_session]

    orthopedic_count = 0
    run_complaints: list[str] = []
    injury_areas = {f.lower() for f in profile.injury_flags}
    for c in w7:
        if c.sport != Sport.RUN:
            continue
        for f in c.fatigue_flags:
            if _matches_keywords(f, spec.orthopedic_keywords):
                run_complaints.append(f)
            if injury_areas and any(area in f.lower() for area in injury_areas):
                run_complaints.append(f)
    for f in _weekly_fatigue_flags(weekly_context):
        if _matches_keywords(f, spec.orthopedic_keywords):
            run_complaints.append(f)
        if injury_areas and any(area in f.lower() for area in injury_areas):
            run_complaints.append(f)
    orthopedic_count = len(run_complaints)
    has_orthopedic = orthopedic_count >= 1

    gi_sessions = 0
    for c in w7:
        for f in c.fatigue_flags:
            if _matches_keywords(f, spec.gi_keywords):
                gi_sessions += 1
                break
    if gi_sessions == 0:
        for f in _weekly_fatigue_flags(weekly_context):
            if _matches_keywords(f, spec.gi_keywords):
                gi_sessions += 1
                break
    has_gi = gi_sessions >= 1
    gi_all = gi_sessions >= spec.gut_training.systemic_session_threshold

    all_rpe_ok = all(
        (c.rpe is None or c.rpe < spec.thresholds.high_rpe) for c in completed
    )
    all_done = len(missed) == 0 and len(w7) > 0

    insufficient = (
        len(completed) < t.min_completed_sessions
        or len(key_completed) < t.min_key_completed_sessions
    )
    partial = len(w7) < t.partial_week_min_sessions

    illness = illness_days_off >= t.illness_days_off_threshold

    # Check prior week for flags (simplified: any flags in broader 14d window)
    if w14_prior:
        prior_high = sum(
            1 for c in w14_prior
            if c.rpe is not None and c.rpe >= spec.thresholds.high_rpe
        )
        prior_fatigue = sum(1 for c in w14_prior if c.fatigue_flags)
        prior_missed = sum(1 for c in w14_prior if not c.completed)
        prior_flags = prior_high >= 2 or prior_fatigue > 0 or prior_missed > 0

    flag_count = len(flags) if flags else int(weighted)

    return SignalSummary(
        flag_count=flag_count,
        flag_messages=flags,
        weighted_flags=weighted,
        completed_count=len(completed),
        key_completed_count=len(key_completed),
        missed_key_count=sum(1 for m in missed if m.is_key_session),
        high_rpe_sessions=len(high_rpe),
        low_readiness_sessions=len(low_read),
        has_orthopedic_stress=has_orthopedic,
        orthopedic_session_count=orthopedic_count,
        has_gi_stress=has_gi,
        gi_session_count=gi_sessions,
        gi_all_sessions=gi_all,
        all_rpe_below_high=all_rpe_ok,
        all_completed=all_done,
        insufficient_data=insufficient,
        partial_week=partial,
        illness_reentry=illness,
        prior_week_had_flags=prior_flags,
    )
