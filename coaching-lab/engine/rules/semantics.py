"""Workout classification and shared thresholds for rule enforcement."""

from __future__ import annotations

from engine.models import PhaseName, PurposeTag, Sport, Workout

# Volume split (Friel baseline) — RIDE-025
DISCIPLINE_SPLIT: dict[Sport, float] = {
    Sport.SWIM: 0.20,
    Sport.BIKE: 0.50,
    Sport.RUN: 0.30,
}

# Duration thresholds (seconds)
LONG_RIDE_MIN_SECONDS = 3 * 3600
LONG_RIDE_PEAK_MAX_SECONDS = 6 * 3600
LONG_RUN_MIN_SECONDS = 90 * 60
LONG_RUN_MAX_SECONDS = int(2.5 * 3600)  # RUN-030
MARATHON_DISTANCE_METERS = 42_195  # RUN-031
TRANSITION_RUN_MAX_SECONDS = 20 * 60  # RIDE-026 / BRK-037
BRICK_RUN_MAX_OFF_LONG_RIDE = 90 * 60  # BRK-039
PEAK_SIM_RIDE_MIN_SECONDS = 4 * 3600
PEAK_SIM_RUN_MIN_SECONDS = 60 * 60

# Spacing (calendar days between session days)
MIN_DAYS_HARD_SAME_DISCIPLINE = 2  # SCH-001 (48 h)
MIN_DAYS_LONG_BIKE_AND_LONG_RUN = 2  # SCH-005
MIN_DAYS_DEMANDING = 1  # SCH-003 (24 h)
MIN_DAYS_HARD_BIKE_BEFORE_LONG_RIDE = 2  # SCH-012
MIN_DAYS_KEY_RUN_AFTER_HARDEST_RIDE = 2  # SCH-002
MIN_DAYS_BETWEEN_BRICKS = 2  # SCH-009
MAX_BRICKS_PER_WEEK = 2  # SCH-010

# Deload — PER-048
DELOAD_VOLUME_FACTOR = 0.65  # ~35% reduction

# Intensity — INT-043 / INT-044
EASY_INTENSITY_MIN_FRACTION = 0.80
MANDATORY_8020_WEEKLY_HOURS = 15.0
RECOMMENDED_8020_WEEKLY_HOURS = 7.0

EASY_PURPOSES = frozenset(
    {
        PurposeTag.AEROBIC_BASE,
        PurposeTag.RECOVERY,
        PurposeTag.ECONOMY,
        PurposeTag.FUELING,
        PurposeTag.STRENGTH,
    }
)
HARD_PURPOSES = frozenset(
    {
        PurposeTag.THRESHOLD,
        PurposeTag.VO2,
        PurposeTag.RACE_EXECUTION,
        PurposeTag.DURABILITY,
    }
)
DEMANDING_PURPOSES = HARD_PURPOSES | frozenset({PurposeTag.FUELING})

# Taper — TAP-052 / TAP-053
TAPER_NO_LONG_RUN_DAYS = 10
TAPER_NO_LONG_BIKE_DAYS = 7

# Macrocycle — RIDE-027 / BRK-042
BIG_DAY_WEEKS_BEFORE_RACE = (11, 5)
MAX_PEAK_SIM_BRICKS_FINAL_6_WEEKS = 2
MAX_STANDALONE_LONG_RUNS_PER_4_WEEKS = 3  # RUN-036


def duration_seconds(workout: Workout) -> int:
    return workout.estimated_duration_seconds or 0


def day_of_week(workout: Workout) -> int | None:
    return workout.day_of_week


def calendar_day_gap(day_a: int, day_b: int) -> int:
    """Minimum forward calendar days from day_a to day_b (0=Mon..6=Sun)."""
    return (day_b - day_a) % 7


def is_rest_day(workouts_on_day: list[Workout]) -> bool:
    return len(workouts_on_day) == 0


def is_brick(workout: Workout) -> bool:
    return workout.sport == Sport.BRICK


def is_hard_purpose(purpose: PurposeTag) -> bool:
    return purpose in HARD_PURPOSES


def is_easy_purpose(purpose: PurposeTag) -> bool:
    return purpose in EASY_PURPOSES


def is_hard_session(workout: Workout) -> bool:
    if is_hard_purpose(workout.purpose_tag):
        return True
    # Key long aerobic sessions are still easy intensity for 80/20 purposes.
    if workout.is_key_session and workout.purpose_tag in (
        PurposeTag.AEROBIC_BASE,
        PurposeTag.RECOVERY,
        PurposeTag.ECONOMY,
        PurposeTag.FUELING,
    ):
        return False
    return workout.is_key_session and workout.purpose_tag in (
        PurposeTag.THRESHOLD,
        PurposeTag.VO2,
        PurposeTag.RACE_EXECUTION,
    )


def is_demanding_session(workout: Workout) -> bool:
    if is_hard_session(workout):
        return True
    if is_long_ride(workout) or is_long_run(workout):
        return True
    return is_brick(workout)


def is_long_ride(workout: Workout) -> bool:
    if workout.sport != Sport.BIKE:
        return False
    if workout.bank_workout_id and workout.bank_workout_id.startswith("LR"):
        return True
    if workout.is_key_session and "long" in workout.title.lower():
        return True
    return duration_seconds(workout) >= LONG_RIDE_MIN_SECONDS


def is_long_run(workout: Workout) -> bool:
    if workout.sport != Sport.RUN:
        return False
    if workout.bank_workout_id and workout.bank_workout_id.startswith("LR"):
        return True
    if workout.is_key_session and "long" in workout.title.lower():
        return True
    return duration_seconds(workout) >= LONG_RUN_MIN_SECONDS


def is_transition_run(workout: Workout) -> bool:
    if workout.sport not in (Sport.RUN, Sport.BRICK):
        return False
    return duration_seconds(workout) <= TRANSITION_RUN_MAX_SECONDS


def is_race_sim_brick(workout: Workout) -> bool:
    if not is_brick(workout):
        return False
    return (
        duration_seconds(workout) >= PEAK_SIM_RIDE_MIN_SECONDS + PEAK_SIM_RUN_MIN_SECONDS
        or workout.purpose_tag == PurposeTag.RACE_EXECUTION
    )


def is_quality_session(workout: Workout) -> bool:
    return workout.is_key_session and is_hard_purpose(workout.purpose_tag)


def primary_sport(workout: Workout) -> Sport:
    if is_brick(workout):
        return Sport.BRICK
    return workout.sport


def workouts_by_day(workouts: list[Workout]) -> dict[int, list[Workout]]:
    grouped: dict[int, list[Workout]] = {d: [] for d in range(7)}
    for w in workouts:
        if w.day_of_week is not None:
            grouped[w.day_of_week].append(w)
    return grouped


def easy_time_fraction(workouts: list[Workout]) -> float:
    total = sum(duration_seconds(w) for w in workouts)
    if total == 0:
        return 1.0
    easy = sum(
        duration_seconds(w)
        for w in workouts
        if not is_hard_session(w) and w.purpose_tag != PurposeTag.RACE_EXECUTION
    )
    return easy / total


def phase_allows_race_sim_brick(phase: PhaseName) -> bool:
    return phase in (PhaseName.BUILD, PhaseName.PEAK)


def phase_allows_transition_brick(phase: PhaseName) -> bool:
    return phase in (PhaseName.BASE, PhaseName.BUILD, PhaseName.PEAK, PhaseName.PREP)
