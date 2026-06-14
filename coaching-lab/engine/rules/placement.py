"""Build a single training week that satisfies the Ironman ruleset."""

from __future__ import annotations

import uuid
from typing import Iterable

from engine.models import (
    AthleteProfile,
    PhaseName,
    PlannedWeek,
    PurposeTag,
    Sport,
    StrengthExercise,
    StrengthPlan,
    Workout,
    WorkoutStatus,
)
from engine.rules import semantics as sem

PREFERRED_REST_DAY = 0  # Monday
PREFERRED_LONG_RIDE_DAY = 5  # Saturday
PREFERRED_LONG_RUN_DAY = 2  # Wednesday (48h+ from Sat ride via Sun, Mon gap)


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


def _week_target_hours(
    base_hours: float,
    week_in_phase_ratio: float,
    is_deload: bool,
) -> float:
    progressed = base_hours * (1.0 + 0.15 * week_in_phase_ratio)
    if is_deload:
        return round(progressed * sem.DELOAD_VOLUME_FACTOR, 1)
    return round(progressed, 1)


def _workout(
    sport: Sport,
    day: int,
    hours: float,
    purpose: PurposeTag,
    is_key: bool,
    title: str,
    *,
    fueling_notes: str | None = None,
    distance_meters: float | None = None,
) -> Workout:
    return Workout(
        id=_new_id(),
        sport=sport,
        title=title,
        day_of_week=day,
        purpose_tag=purpose,
        is_key_session=is_key,
        estimated_duration_seconds=max(1, int(hours * 3600)),
        estimated_distance_meters=distance_meters,
        fueling_notes=fueling_notes,
        status=WorkoutStatus.PLANNED,
    )


def _pick_day(
    candidates: Iterable[int],
    available: list[int],
    fallback: int,
    reserved: set[int] | None = None,
) -> int:
    blocked = reserved or set()
    for day in candidates:
        if day in available and day not in blocked:
            return day
    for day in available:
        if day not in blocked:
            return day
    return fallback


def _days_with_gap(from_day: int, min_gap: int, available: list[int]) -> list[int]:
    return [d for d in available if sem.calendar_day_gap(from_day, d) >= min_gap]


def _is_brick_week(
    week_number: int,
    phase: PhaseName,
    total_weeks: int,
    limiter_is_run: bool,
) -> bool:
    if phase not in (PhaseName.BUILD, PhaseName.PEAK):
        return False
    big_days = {
        total_weeks - offset + 1
        for offset in sem.BIG_DAY_WEEKS_BEFORE_RACE
        if total_weeks - offset + 1 >= 1
    }
    if week_number in big_days:
        return True
    # Race-sim brick every 3rd build week when run is not the limiter focus week
    if phase == PhaseName.BUILD and week_number % 3 == 0 and not limiter_is_run:
        return True
    return False


def _long_ride_duration(phase: PhaseName, target_hours: float, is_deload: bool) -> float:
    if is_deload or phase == PhaseName.TAPER:
        return min(2.5, target_hours * sem.DISCIPLINE_SPLIT[Sport.BIKE] * 0.7)
    if phase in (PhaseName.PREP, PhaseName.BASE):
        return min(3.5, target_hours * sem.DISCIPLINE_SPLIT[Sport.BIKE] * 0.55)
    if phase == PhaseName.PEAK:
        return min(6.0, max(4.5, target_hours * sem.DISCIPLINE_SPLIT[Sport.BIKE] * 0.6))
    return min(5.0, max(3.5, target_hours * sem.DISCIPLINE_SPLIT[Sport.BIKE] * 0.58))


def _long_run_duration(phase: PhaseName, target_hours: float, is_deload: bool) -> float:
    raw = target_hours * sem.DISCIPLINE_SPLIT[Sport.RUN] * 0.55
    if is_deload or phase == PhaseName.TAPER:
        raw *= 0.7
    return min(2.5, max(1.25, raw))


def schedule_week(
    week_number: int,
    phase: PhaseName,
    is_deload: bool,
    profile: AthleteProfile,
    strength_plan: StrengthPlan,
    strength_exercises: list[StrengthExercise],
    week_in_phase_ratio: float = 0.5,
    total_weeks: int = 24,
) -> PlannedWeek:
    """Place sessions for one week obeying all hard scheduling rules."""
    target_hours = _week_target_hours(profile.weekly_hours, week_in_phase_ratio, is_deload)
    available = sorted(profile.available_days) or list(range(7))
    limiter_is_run = profile.limiter_discipline == Sport.RUN
    brick_week = _is_brick_week(week_number, phase, total_weeks, limiter_is_run)

    swim_h = target_hours * sem.DISCIPLINE_SPLIT[Sport.SWIM]
    bike_h = target_hours * sem.DISCIPLINE_SPLIT[Sport.BIKE]
    run_h = target_hours * sem.DISCIPLINE_SPLIT[Sport.RUN]

    workouts: list[Workout] = []
    reserved: set[int] = set()

    # Rest day — SCH-018 (must stay empty; prefer not stealing the long-ride day)
    ride_day_options = [d for d in (PREFERRED_LONG_RIDE_DAY, 6, 4, 5) if d in available]
    rest_pool = [d for d in available if d not in ride_day_options] or list(available)
    rest_day = _pick_day([PREFERRED_REST_DAY, 4, 1, 3], rest_pool, available[0])
    reserved.add(rest_day)

    long_ride_day = _pick_day(
        [PREFERRED_LONG_RIDE_DAY, 6, 4, 5],
        available,
        available[-1],
        reserved,
    )
    reserved.add(long_ride_day)
    long_ride_hours = _long_ride_duration(phase, target_hours, is_deload)
    long_run_day: int | None = None

    if brick_week and sem.phase_allows_race_sim_brick(phase):
        # BRK-041: brick week replaces separate long ride + long run
        brick_hours = min(
            long_ride_hours + 1.25,
            (sem.PEAK_SIM_RIDE_MIN_SECONDS + sem.PEAK_SIM_RUN_MIN_SECONDS) / 3600,
        )
        workouts.append(
            _workout(
                Sport.BRICK,
                long_ride_day,
                brick_hours,
                PurposeTag.RACE_EXECUTION,
                True,
                "Race simulation brick",
                fueling_notes="Race fueling rehearsal: 60–90 g carbs/hr from minute 10.",
            )
        )
        anchor_days = set(reserved) | {long_ride_day}
        long_run_day = None
    else:
        fueling = "Race fueling rehearsal: 60–90 g carbs/hr from minute 10; practice race products."
        transition_min = 0.0
        if (
            sem.phase_allows_transition_brick(phase)
            and not is_deload
            and week_number % 2 == 0
        ):
            transition_min = 15 / 60  # RIDE-026: optional 15 min off long ride

        workouts.append(
            _workout(
                Sport.BIKE,
                long_ride_day,
                long_ride_hours + transition_min,
                PurposeTag.AEROBIC_BASE,
                True,
                "Long ride",
                fueling_notes=fueling,
            )
        )
        anchor_days = set(reserved) | {long_ride_day}

        # Long run — SCH-005: ≥2 days from long ride
        long_run_candidates = _days_with_gap(
            long_ride_day, sem.MIN_DAYS_LONG_BIKE_AND_LONG_RUN, available
        )
        long_run_day = _pick_day(
            [PREFERRED_LONG_RUN_DAY, 1, 3],
            [d for d in long_run_candidates if d not in anchor_days],
            long_run_candidates[0] if long_run_candidates else (long_ride_day + 2) % 7,
            anchor_days,
        )
        long_run_hours = _long_run_duration(phase, target_hours, is_deload)
        include_race_pace = sem.calendar_day_gap(long_ride_day, long_run_day) >= sem.MIN_DAYS_LONG_BIKE_AND_LONG_RUN
        run_purpose = (
            PurposeTag.RACE_EXECUTION
            if include_race_pace and phase in (PhaseName.BUILD, PhaseName.PEAK)
            else PurposeTag.AEROBIC_BASE
        )
        workouts.append(
            _workout(
                Sport.RUN,
                long_run_day,
                long_run_hours,
                run_purpose,
                True,
                "Long run",
            )
        )
        anchor_days.add(long_run_day)

    # Hard bike — SCH-012: ≥2 days before long ride
    hard_bike_candidates = [
        d
        for d in available
        if d not in anchor_days
        and sem.calendar_day_gap(d, long_ride_day) >= sem.MIN_DAYS_HARD_BIKE_BEFORE_LONG_RIDE
    ]
    if hard_bike_candidates and phase in (PhaseName.BUILD, PhaseName.PEAK) and not is_deload:
        hard_bike_day = _pick_day([1, 2, 3], hard_bike_candidates, hard_bike_candidates[0])
        workouts.append(
            _workout(
                Sport.BIKE,
                hard_bike_day,
                min(1.25, bike_h * 0.22),
                PurposeTag.THRESHOLD,
                True,
                "Bike threshold",
            )
        )
        anchor_days.add(hard_bike_day)

    # Key run quality — SCH-002: ≥2 days after long ride
    if not brick_week and long_run_day is not None:
        key_run_candidates = _days_with_gap(
            long_ride_day, sem.MIN_DAYS_KEY_RUN_AFTER_HARDEST_RIDE, available
        )
        key_run_candidates = [
            d
            for d in key_run_candidates
            if d not in anchor_days
            and d != long_run_day
            and d not in (0, 1)  # SCH-007: protect Mon–Tue after weekend
        ]
        if key_run_candidates and phase in (PhaseName.BUILD, PhaseName.PEAK) and not is_deload:
            key_run_day = _pick_day([3, 4], key_run_candidates, key_run_candidates[0])
            workouts.append(
                _workout(
                    Sport.RUN,
                    key_run_day,
                    min(0.75, run_h * 0.2),
                    PurposeTag.THRESHOLD,
                    True,
                    "Run threshold",
                )
            )
            anchor_days.add(key_run_day)

    training_days = [d for d in available if d != rest_day]
    max_runs = 2 if len(training_days) <= 3 else 3

    # Supporting easy sessions — RUN-033
    run_sessions = [w for w in workouts if w.sport == Sport.RUN]
    if len(run_sessions) < 2:
        easy_run_day = _pick_day(
            [4, 3, 2],
            [
                d
                for d in training_days
                if d != long_run_day and d != long_ride_day
            ],
            training_days[0],
        )
        workouts.append(
            _workout(
                Sport.RUN,
                easy_run_day,
                min(0.75, run_h * 0.18),
                PurposeTag.AEROBIC_BASE,
                False,
                "Easy run",
            )
        )
    elif len(run_sessions) < max_runs and phase != PhaseName.TAPER:
        filler = _pick_day(
            [4, 3],
            [d for d in training_days if d not in {long_run_day, long_ride_day}],
            training_days[0],
        )
        workouts.append(
            _workout(
                Sport.RUN,
                filler,
                min(0.5, run_h * 0.12),
                PurposeTag.AEROBIC_BASE,
                False,
                "Easy run",
            )
        )

    # Easy bike filler (not on long ride day)
    easy_bike_day = _pick_day(
        [3, 4, 1],
        [d for d in training_days if d != long_ride_day],
        training_days[0],
    )
    if not any(w.sport == Sport.BIKE and w.day_of_week == easy_bike_day for w in workouts):
        workouts.append(
            _workout(
                Sport.BIKE,
                easy_bike_day,
                min(1.0, bike_h * 0.18),
                PurposeTag.AEROBIC_BASE,
                False,
                "Endurance ride",
            )
        )

    # Swim — may share a day with easy aerobic work
    swim_sessions = 1 if len(training_days) <= 3 else (2 if target_hours >= 6 else 1)
    swim_days = _pick_days_spaced(training_days, swim_sessions)
    for i, day in enumerate(swim_days):
        workouts.append(
            _workout(
                Sport.SWIM,
                day,
                swim_h / max(1, swim_sessions),
                PurposeTag.ECONOMY if i == 0 else PurposeTag.AEROBIC_BASE,
                i == 0,
                "Swim technique" if i == 0 else "Swim endurance",
            )
        )

    # Brick week still needs 2 runs — RUN-033
    if brick_week:
        run_count = sum(1 for w in workouts if w.sport == Sport.RUN)
        while run_count < 2:
            day = _pick_day([2, 3, 4], training_days, training_days[0])
            workouts.append(
                _workout(
                    Sport.RUN,
                    day,
                    min(0.6, run_h * 0.15),
                    PurposeTag.AEROBIC_BASE,
                    False,
                    "Easy run",
                )
            )
            run_count += 1

    # Strength — SCH-020
    long_run_day_for_strength = next(
        (w.day_of_week for w in workouts if sem.is_long_run(w)),
        None,
    )
    strength_blocked = set()
    if long_run_day_for_strength is not None:
        strength_blocked.add(long_run_day_for_strength)
        strength_blocked.add((long_run_day_for_strength - 1) % 7)
    strength_days = _pick_days_spaced(
        [
            d
            for d in training_days
            if d not in strength_blocked
        ],
        strength_plan.sessions_per_week,
    )
    for day in strength_days:
        workouts.append(
            Workout(
                id=_new_id(),
                sport=Sport.STRENGTH,
                title="Strength session",
                description=strength_plan.focus,
                day_of_week=day,
                purpose_tag=PurposeTag.STRENGTH,
                is_key_session=False,
                exercises=strength_exercises,
                estimated_duration_seconds=strength_plan.session_duration_minutes * 60,
                status=WorkoutStatus.PLANNED,
            )
        )

    workouts.sort(key=lambda w: (w.day_of_week if w.day_of_week is not None else 99, w.sport.value))
    _normalize_discipline_split(workouts, target_hours)
    _apply_duration_caps(workouts)
    _normalize_discipline_split(workouts, target_hours)
    return PlannedWeek(
        week_number=week_number,
        phase=phase,
        is_deload=is_deload,
        target_hours=target_hours,
        workouts=workouts,
    )


def _pick_days_spaced(days: list[int], n: int) -> list[int]:
    if not days or n <= 0:
        return []
    if n >= len(days):
        return days[:n]
    step = len(days) / n
    return [days[int(i * step)] for i in range(n)]


def _normalize_discipline_split(workouts: list[Workout], target_hours: float) -> None:
    """Scale endurance session durations to swim 20 / bike 50 / run 30 (RIDE-025)."""
    target_seconds = int(target_hours * 3600)
    if target_seconds <= 0:
        return

    def bucket(w: Workout) -> Sport:
        if w.sport == Sport.BRICK:
            return Sport.BIKE
        return w.sport

    endurance = [w for w in workouts if w.sport != Sport.STRENGTH]
    if not endurance:
        return

    targets = {
        Sport.SWIM: target_seconds * sem.DISCIPLINE_SPLIT[Sport.SWIM],
        Sport.BIKE: target_seconds * sem.DISCIPLINE_SPLIT[Sport.BIKE],
        Sport.RUN: target_seconds * sem.DISCIPLINE_SPLIT[Sport.RUN],
    }
    actual = {s: 0 for s in targets}
    groups: dict[Sport, list[Workout]] = {s: [] for s in targets}
    for w in endurance:
        sport = bucket(w)
        if sport in groups:
            groups[sport].append(w)
            actual[sport] += w.estimated_duration_seconds or 0

    for sport, group in groups.items():
        if not group or actual[sport] <= 0:
            continue
        scale = targets[sport] / actual[sport]
        for w in group:
            w.estimated_duration_seconds = max(
                1, int((w.estimated_duration_seconds or 0) * scale)
            )

    # Re-apply hard duration caps after scaling — RUN-030 / RIDE-024
    _apply_duration_caps(workouts)


def _apply_duration_caps(workouts: list[Workout]) -> None:
    for w in workouts:
        if sem.is_long_run(w):
            w.estimated_duration_seconds = min(
                w.estimated_duration_seconds or 0,
                sem.LONG_RUN_MAX_SECONDS,
            )
        if sem.is_long_ride(w):
            w.estimated_duration_seconds = min(
                w.estimated_duration_seconds or 0,
                sem.LONG_RIDE_PEAK_MAX_SECONDS,
            )
