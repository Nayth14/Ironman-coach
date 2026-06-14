"""Strength prescription from the onboarding profile (ADR-014).

Deterministic. Injury-safe exercise selection is rule-based, not LLM-guessed.
"""

from __future__ import annotations

from engine.models import (
    AthleteProfile,
    PhaseName,
    StrengthBackground,
    StrengthEquipment,
    StrengthExercise,
    StrengthPlan,
)

# Exercise pool tagged by equipment requirement and the body areas they load.
# `loads` is used to filter against injury restrictions.
# `phase_tags` hints which phases prefer this exercise (empty = all phases).
_EXERCISE_POOL: list[dict] = [
    {"name": "Goblet squat", "equipment": "home", "loads": ["knee"], "sets": 3, "reps": "8-12", "phase_tags": ["build", "peak"]},
    {"name": "Back squat", "equipment": "gym", "loads": ["knee", "back"], "sets": 4, "reps": "5-8", "phase_tags": ["build", "peak"]},
    {"name": "Split squat", "equipment": "home", "loads": ["knee"], "sets": 3, "reps": "8-10/side", "phase_tags": ["build", "peak", "base"]},
    {"name": "Romanian deadlift", "equipment": "home", "loads": ["back"], "sets": 3, "reps": "8-10", "phase_tags": ["build", "peak", "base"]},
    {"name": "Conventional deadlift", "equipment": "gym", "loads": ["back"], "sets": 4, "reps": "4-6", "phase_tags": ["build", "peak"]},
    {"name": "Single-leg glute bridge", "equipment": "minimal", "loads": [], "sets": 3, "reps": "12/side", "phase_tags": []},
    {"name": "Step-up", "equipment": "minimal", "loads": ["knee"], "sets": 3, "reps": "10/side", "phase_tags": ["base", "build"]},
    {"name": "Overhead press", "equipment": "gym", "loads": ["shoulder"], "sets": 3, "reps": "6-10", "phase_tags": ["build", "peak"]},
    {"name": "Push-up", "equipment": "minimal", "loads": ["shoulder"], "sets": 3, "reps": "8-15", "phase_tags": []},
    {"name": "Band pull-apart", "equipment": "minimal", "loads": [], "sets": 3, "reps": "15", "phase_tags": ["taper", "prep"]},
    {"name": "Plank", "equipment": "minimal", "loads": [], "sets": 3, "reps": "30-45s", "phase_tags": ["taper", "prep"]},
    {"name": "Side plank", "equipment": "minimal", "loads": [], "sets": 3, "reps": "30s/side", "phase_tags": ["taper"]},
    {"name": "Dead bug", "equipment": "minimal", "loads": [], "sets": 3, "reps": "10/side", "phase_tags": ["taper", "prep"]},
    {"name": "Calf raise", "equipment": "minimal", "loads": [], "sets": 3, "reps": "15-20", "phase_tags": []},
    {"name": "Bird dog", "equipment": "minimal", "loads": [], "sets": 3, "reps": "10/side", "phase_tags": ["taper", "prep"]},
]

_EQUIPMENT_RANK = {
    StrengthEquipment.MINIMAL: ["minimal"],
    StrengthEquipment.HOME: ["minimal", "home"],
    StrengthEquipment.GYM: ["minimal", "home", "gym"],
}

# Map free-text injury flags to body areas we restrict.
_INJURY_AREA_KEYWORDS = {
    "knee": "knee",
    "back": "back",
    "spine": "back",
    "lumbar": "back",
    "shoulder": "shoulder",
    "rotator": "shoulder",
}

_DELOAD_DURATION_FACTOR = 0.80


def _restricted_areas(profile: AthleteProfile) -> set[str]:
    areas: set[str] = set()
    for flag in profile.injury_flags:
        low = flag.lower()
        for keyword, area in _INJURY_AREA_KEYWORDS.items():
            if keyword in low:
                areas.add(area)
    return areas


def _sessions_per_week(profile: AthleteProfile, phase: PhaseName) -> int:
    bg = profile.strength_background

    if bg == StrengthBackground.NONE:
        base = 1
    elif bg == StrengthBackground.BEGINNER:
        base = 2 if phase in (PhaseName.PREP, PhaseName.BASE) else 1
    elif bg == StrengthBackground.INTERMEDIATE:
        base = 2 if phase in (PhaseName.PREP, PhaseName.BASE) else 1
    else:  # experienced
        base = 2

    if phase == PhaseName.TAPER:
        base = min(base, 1)

    if profile.weekly_hours < 8:
        base = min(base, 1)

    return base


def _session_duration(profile: AthleteProfile) -> int:
    if profile.weekly_hours < 8:
        return 25
    if profile.strength_background in (StrengthBackground.NONE, StrengthBackground.BEGINNER):
        return 30
    return 40


def _phase_focus(profile: AthleteProfile, phase: PhaseName) -> str:
    if phase == PhaseName.TAPER:
        return "Mobility and core activation — keep it light before race day"
    if phase == PhaseName.PREP:
        return "Movement quality and durability with bodyweight basics"
    if phase in (PhaseName.BUILD, PhaseName.PEAK):
        if profile.strength_background == StrengthBackground.EXPERIENCED:
            return "Compound lower-body strength and power maintenance for race readiness"
        return "Compound lower-body strength plus core stability for run durability"
    if profile.strength_background == StrengthBackground.NONE:
        return "Movement quality and durability with bodyweight basics"
    return "Aerobic-phase strength: build durability without excess fatigue"


def _exercise_sort_key(ex: dict, phase: PhaseName) -> tuple[int, str]:
    """Prefer exercises tagged for the current phase."""
    phase_val = phase.value
    tags = ex.get("phase_tags") or []
    if not tags:
        return (1, ex["name"])
    if phase_val in tags:
        return (0, ex["name"])
    return (2, ex["name"])


def select_exercises(
    profile: AthleteProfile,
    phase: PhaseName = PhaseName.BASE,
    max_count: int = 6,
) -> list[StrengthExercise]:
    """Pick injury-safe exercises matching available equipment and phase."""
    restricted = _restricted_areas(profile)
    allowed_equipment = _EQUIPMENT_RANK[profile.strength_equipment]

    candidates: list[dict] = []
    for ex in _EXERCISE_POOL:
        if ex["equipment"] not in allowed_equipment:
            continue
        if restricted.intersection(ex["loads"]):
            continue
        candidates.append(ex)

    candidates.sort(key=lambda ex: _exercise_sort_key(ex, phase))

    selected: list[StrengthExercise] = []
    for ex in candidates:
        selected.append(
            StrengthExercise(
                name=ex["name"],
                sets=ex["sets"],
                reps=ex["reps"],
                restriction_safe=True,
            )
        )
        if len(selected) >= max_count:
            break

    return selected


def prescribe(profile: AthleteProfile, phase: PhaseName = PhaseName.BASE) -> StrengthPlan:
    """Build a strength prescription for a given phase."""
    spw = _sessions_per_week(profile, phase)
    duration = _session_duration(profile)
    restricted = _restricted_areas(profile)
    focus = _phase_focus(profile, phase)

    restrictions = sorted(restricted)
    if restrictions:
        restriction_note = (
            f"Avoiding {', '.join(restrictions)} loading per injury history."
        )
    else:
        restriction_note = "No injury restrictions."

    rationale = (
        f"{spw}x/week, {duration} min ({phase.value} phase). "
        f"Background: {profile.strength_background.value}; "
        f"equipment: {profile.strength_equipment.value}. {restriction_note}"
    )

    return StrengthPlan(
        sessions_per_week=spw,
        session_duration_minutes=duration,
        focus=focus,
        restrictions=restrictions,
        rationale=rationale,
    )


def prescribe_for_week(
    profile: AthleteProfile,
    phase: PhaseName,
    is_deload: bool = False,
) -> StrengthPlan:
    """Phase-aware prescription with optional deload scaling."""
    plan = prescribe(profile, phase)
    if is_deload:
        scaled_duration = max(
            20,
            int(plan.session_duration_minutes * _DELOAD_DURATION_FACTOR),
        )
        return plan.model_copy(
            update={
                "session_duration_minutes": scaled_duration,
                "rationale": plan.rationale + " Deload week: reduced session length.",
            }
        )
    return plan
