"""Macrocycle periodization: split the available weeks into phases.

Prep -> Base -> Build -> Peak -> Taper, built backward from race day.
Deterministic.
"""

from __future__ import annotations

from engine.models import (
    AthleteProfile,
    ExperienceLevel,
    Phase,
    PhaseName,
)

# Ideal phase proportions (of total weeks), excluding the fixed taper.
# Taper is fixed at the end; remaining weeks distributed across prep/base/build/peak.
_PHASE_PROPORTIONS = {
    PhaseName.PREP: 0.12,
    PhaseName.BASE: 0.45,
    PhaseName.BUILD: 0.30,
    PhaseName.PEAK: 0.13,
}

_PHASE_OBJECTIVES = {
    PhaseName.PREP: "Reset, consistency, technique, and movement quality.",
    PhaseName.BASE: "Build the aerobic engine and durability with high easy volume.",
    PhaseName.BUILD: "Specific endurance and race execution with race-pace work and bricks.",
    PhaseName.PEAK: "Sharpen with race simulation while managing fatigue.",
    PhaseName.TAPER: "Shed fatigue, keep frequency and sharpness, arrive fresh.",
}


def _taper_weeks(total_weeks: int) -> int:
    if total_weeks >= 16:
        return 3
    if total_weeks >= 10:
        return 2
    return 1


def build_phases(profile: AthleteProfile, total_weeks: int) -> list[Phase]:
    """Allocate phases across the available weeks."""
    total_weeks = max(4, total_weeks)
    taper = _taper_weeks(total_weeks)
    remaining = total_weeks - taper

    # Beginners get relatively more base; advanced get more build/peak.
    proportions = dict(_PHASE_PROPORTIONS)
    if profile.experience_level == ExperienceLevel.BEGINNER:
        proportions[PhaseName.BASE] += 0.08
        proportions[PhaseName.BUILD] -= 0.05
        proportions[PhaseName.PEAK] -= 0.03
    elif profile.experience_level == ExperienceLevel.ADVANCED:
        proportions[PhaseName.BASE] -= 0.05
        proportions[PhaseName.BUILD] += 0.03
        proportions[PhaseName.PEAK] += 0.02

    # Allocate integer weeks proportionally.
    ordered = [PhaseName.PREP, PhaseName.BASE, PhaseName.BUILD, PhaseName.PEAK]
    raw = {p: proportions[p] * remaining for p in ordered}
    alloc = {p: max(1, int(round(raw[p]))) for p in ordered}

    # Fix rounding drift so the phases sum to `remaining`.
    drift = remaining - sum(alloc.values())
    # Apply drift to BASE (the most elastic phase).
    alloc[PhaseName.BASE] = max(1, alloc[PhaseName.BASE] + drift)

    phases: list[Phase] = []
    cursor = 1
    for p in ordered:
        weeks = alloc[p]
        phases.append(
            Phase(
                name=p,
                start_week=cursor,
                end_week=cursor + weeks - 1,
                objective=_PHASE_OBJECTIVES[p],
            )
        )
        cursor += weeks

    phases.append(
        Phase(
            name=PhaseName.TAPER,
            start_week=cursor,
            end_week=cursor + taper - 1,
            objective=_PHASE_OBJECTIVES[PhaseName.TAPER],
        )
    )

    return phases


def phase_for_week(phases: list[Phase], week_number: int) -> PhaseName:
    for phase in phases:
        if phase.start_week <= week_number <= phase.end_week:
            return phase.name
    return phases[-1].name


def is_deload_week(week_number: int, phase: PhaseName) -> bool:
    """Every 4th week is a deload, except during taper (already reduced)."""
    if phase == PhaseName.TAPER:
        return False
    return week_number % 4 == 0
