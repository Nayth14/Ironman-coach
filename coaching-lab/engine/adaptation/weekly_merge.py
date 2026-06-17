"""Merge weekly narrative context for signal aggregation."""

from __future__ import annotations

from engine.models import WeeklyContext


def merge_weekly_context(
    base: WeeklyContext | None,
    augmentations: WeeklyContext | None,
) -> WeeklyContext | None:
    if not base and not augmentations:
        return None
    if not augmentations:
        return base
    if not base:
        return augmentations

    flags = sorted(set(base.fatigue_flags) | set(augmentations.fatigue_flags))
    quotes = list(dict.fromkeys(base.athlete_quotes + augmentations.athlete_quotes))
    summary = augmentations.summary or base.summary
    return WeeklyContext(
        week_number=base.week_number or augmentations.week_number,
        summary=summary,
        fatigue_flags=flags,
        illness_days_off=max(base.illness_days_off, augmentations.illness_days_off),
        life_stress=base.life_stress or augmentations.life_stress,
        missed_key_reason=augmentations.missed_key_reason or base.missed_key_reason,
        athlete_quotes=quotes,
        confidence=augmentations.confidence if augmentations.confidence != "medium" else base.confidence,
    )
