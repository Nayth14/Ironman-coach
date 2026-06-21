from __future__ import annotations

from collections import defaultdict

from engine.models import PhaseName, PlanState, PurposeTag, Sport, Workout
from engine.rules import semantics as sem
from engine.workout_bank.models import BankWorkout


def is_bank_eligible(workout: Workout, *, is_deload: bool) -> bool:
    if workout.sport == Sport.SWIM:
        return True
    if workout.sport not in (Sport.BIKE, Sport.RUN):
        return False
    if not workout.is_key_session:
        return False
    if is_deload and sem.is_hard_purpose(workout.purpose_tag):
        return False
    return True


def _duration_minutes(workout: Workout) -> int:
    sec = workout.estimated_duration_seconds or 0
    return max(1, round(sec / 60))


def _nearest_duration(candidates: list[BankWorkout], target_minutes: int) -> int:
    durations = sorted({w.duration_minutes for w in candidates})
    if not durations:
        return target_minutes
    return min(durations, key=lambda d: abs(d - target_minutes))


def _choose_family(workout: Workout, phase: PhaseName, week_number: int, is_deload: bool) -> str:
    is_long = sem.is_long_ride(workout) or sem.is_long_run(workout)
    if workout.sport == Sport.SWIM:
        title = workout.title.lower()
        if is_deload or phase == PhaseName.TAPER:
            if workout.purpose_tag == PurposeTag.ECONOMY or "technique" in title:
                return "technique"
            return "aerobic_fitness"
        if workout.purpose_tag == PurposeTag.ECONOMY or "technique" in title:
            return "technique"
        if (
            phase in (PhaseName.BUILD, PhaseName.PEAK)
            and workout.is_key_session
            and sem.is_hard_purpose(workout.purpose_tag)
        ):
            return "threshold_fitness"
        return "aerobic_fitness"
    if workout.sport == Sport.BIKE:
        if is_long:
            if is_deload or phase == PhaseName.TAPER:
                return "long_steady"
            if phase in (PhaseName.PREP, PhaseName.BASE):
                return "long_steady"
            if phase == PhaseName.BUILD:
                return "long_tempo" if week_number % 2 == 0 else "long_race_pace"
            return "long_durability"
        if phase in (PhaseName.PREP, PhaseName.BASE):
            return "sweet_spot"
        return "threshold" if week_number % 2 else "over_under"

    if is_long:
        if is_deload or phase == PhaseName.TAPER:
            return "long_conversational"
        if phase in (PhaseName.PREP, PhaseName.BASE):
            return "long_conversational"
        if phase == PhaseName.BUILD:
            return "long_race_blocks"
        return "long_fast_finish"
    if phase in (PhaseName.PREP, PhaseName.BASE):
        return "tempo"
    if phase == PhaseName.BUILD and week_number % 2 == 0:
        return "fast_interval"
    if phase == PhaseName.PEAK and week_number % 3 == 0:
        return "fast_interval"
    return "tempo"


def pick_bank_workout(
    workout: Workout,
    *,
    phase: PhaseName,
    week_number: int,
    is_deload: bool,
    state: PlanState,
    bank_workouts: list[BankWorkout],
) -> BankWorkout | None:
    family = _choose_family(workout, phase, week_number, is_deload)
    by_sport = [w for w in bank_workouts if w.sport == workout.sport]
    candidates = [w for w in by_sport if w.family == family]
    if not candidates:
        return None

    duration = _nearest_duration(candidates, _duration_minutes(workout))
    candidates = [w for w in candidates if w.duration_minutes == duration]
    if not candidates:
        return None

    used = set(state.used_bank_ids)
    fresh = [w for w in candidates if w.id not in used]
    pool = fresh or candidates
    idx = (week_number + len(workout.id)) % len(pool)
    return pool[idx]


def index_by_sport(bank_workouts: list[BankWorkout]) -> dict[Sport, list[BankWorkout]]:
    out: dict[Sport, list[BankWorkout]] = defaultdict(list)
    for w in bank_workouts:
        out[w.sport].append(w)
    return dict(out)
