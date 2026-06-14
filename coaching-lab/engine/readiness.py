"""Readiness assessment: is the athlete's timeline realistic and safe?

Deterministic rules (not LLM). Produces a green/amber/red verdict and any
adjustments the plan generator should apply.
"""

from __future__ import annotations

from datetime import date

from engine.models import (
    AthleteProfile,
    ExperienceLevel,
    ReadinessResult,
    ReadinessVerdict,
)

# Recommended minimum preparation runway by experience level (weeks).
_MIN_WEEKS = {
    ExperienceLevel.BEGINNER: 24,
    ExperienceLevel.INTERMEDIATE: 16,
    ExperienceLevel.ADVANCED: 12,
}

# Comfortable runway (weeks) above which timeline is not a concern.
_COMFORTABLE_WEEKS = {
    ExperienceLevel.BEGINNER: 30,
    ExperienceLevel.INTERMEDIATE: 20,
    ExperienceLevel.ADVANCED: 16,
}

# Minimum weekly hours we consider workable for Ironman prep.
_MIN_WEEKLY_HOURS = 6.0


def weeks_to_race(race_date: date, today: date | None = None) -> int:
    today = today or date.today()
    return max(0, (race_date - today).days // 7)


def assess(profile: AthleteProfile, today: date | None = None) -> ReadinessResult:
    weeks = weeks_to_race(profile.race_date, today)
    flags: list[str] = []
    adjustments: list[str] = []

    min_weeks = _MIN_WEEKS[profile.experience_level]
    comfortable = _COMFORTABLE_WEEKS[profile.experience_level]

    # Timeline checks
    if weeks < min_weeks * 0.6:
        flags.append(
            f"Only {weeks} weeks to race; well below the ~{min_weeks} weeks "
            f"recommended for a {profile.experience_level.value} athlete."
        )
        adjustments.append("Consider a later race or a finish-focused, conservative plan.")
    elif weeks < min_weeks:
        flags.append(
            f"{weeks} weeks to race is a bit short of the ~{min_weeks} weeks ideal."
        )
        adjustments.append("Compress base phase and prioritize key sessions.")

    # Time availability
    if profile.weekly_hours < _MIN_WEEKLY_HOURS:
        flags.append(
            f"{profile.weekly_hours:.0f} h/week is low for Ironman volume."
        )
        adjustments.append("Cap intensity, protect long sessions, keep strength to 1x/week.")

    # Injury load
    if len(profile.injury_flags) >= 2:
        flags.append(
            f"Multiple injury flags: {', '.join(profile.injury_flags)}."
        )
        adjustments.append("Conservative run loading and injury-safe strength selection.")
    elif len(profile.injury_flags) == 1:
        adjustments.append(
            f"Train around {profile.injury_flags[0]} with modified loading."
        )

    # Verdict
    if not flags and weeks >= comfortable:
        verdict = ReadinessVerdict.GREEN
        rationale = (
            f"{weeks} weeks to {profile.race_name} with {profile.weekly_hours:.0f} h/week "
            f"is a solid runway for a {profile.experience_level.value} athlete."
        )
    elif len(flags) >= 2 or weeks < min_weeks * 0.6:
        verdict = ReadinessVerdict.RED
        rationale = "Significant concerns to address before committing to this race plan."
    else:
        verdict = ReadinessVerdict.AMBER
        rationale = "Workable with some adjustments to keep training safe and realistic."

    return ReadinessResult(
        verdict=verdict,
        weeks_to_race=weeks,
        rationale=rationale + (" " + " ".join(flags) if flags else ""),
        adjustments=adjustments,
    )
