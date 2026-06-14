"""Validate training plans against the Ironman ruleset."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from engine.models import PhaseName, PlannedWeek, Sport, TrainingPlan, Workout
from engine.rules import semantics as sem
from engine.rules.ruleset import RULE_BY_ID, CoachingRule


@dataclass(frozen=True, slots=True)
class RuleContext:
    """Extra context needed for macrocycle-level rules."""

    race_date: date
    total_weeks: int
    all_weeks: tuple[PlannedWeek, ...] = ()
    big_day_week_numbers: frozenset[int] = frozenset()


@dataclass(frozen=True, slots=True)
class RuleViolation:
    rule_id: str
    message: str

    @property
    def rule(self) -> CoachingRule:
        return RULE_BY_ID[self.rule_id]


class RulesetViolationError(Exception):
    """Raised when a plan breaks a hard coaching rule."""

    def __init__(self, violations: list[RuleViolation]) -> None:
        self.violations = violations
        lines = [f"{v.rule_id}: {v.message}" for v in violations]
        super().__init__("Ruleset violations:\n" + "\n".join(lines))


def _violation(rule_id: str, message: str) -> RuleViolation:
    return RuleViolation(rule_id=rule_id, message=message)


def _hardest_ride_or_brick(workouts: list[Workout]) -> Workout | None:
    candidates = [w for w in workouts if sem.is_long_ride(w) or sem.is_race_sim_brick(w)]
    if not candidates:
        candidates = [
            w
            for w in workouts
            if w.sport in (Sport.BIKE, Sport.BRICK) and w.is_key_session
        ]
    if not candidates:
        return None
    return max(candidates, key=sem.duration_seconds)


def _hardest_run(workouts: list[Workout]) -> Workout | None:
    candidates = [w for w in workouts if sem.is_long_run(w)]
    if not candidates:
        candidates = [w for w in workouts if w.sport == Sport.RUN and w.is_key_session]
    if not candidates:
        return None
    return max(candidates, key=sem.duration_seconds)


def validate_week(week: PlannedWeek, ctx: RuleContext | None = None) -> list[RuleViolation]:
    violations: list[RuleViolation] = []
    workouts = week.workouts
    by_day = sem.workouts_by_day(workouts)

    weeks_to_race: int | None = None
    if ctx is not None:
        weeks_to_race = ctx.total_weeks - week.week_number + 1

    # --- Per-workout caps ---
    for w in workouts:
        if sem.is_long_run(w) and sem.duration_seconds(w) > sem.LONG_RUN_MAX_SECONDS:
            violations.append(
                _violation(
                    "RUN-030",
                    f"{w.title} is {sem.duration_seconds(w) // 60} min; max 150 min.",
                )
            )
        if w.sport == Sport.RUN and (w.estimated_distance_meters or 0) >= sem.MARATHON_DISTANCE_METERS:
            violations.append(
                _violation("RUN-031", f"{w.title} reaches marathon distance in training.")
            )
        if sem.is_long_ride(w) and sem.duration_seconds(w) > sem.LONG_RIDE_PEAK_MAX_SECONDS:
            violations.append(
                _violation(
                    "RIDE-024",
                    f"{w.title} is {sem.duration_seconds(w) // 3600} h; max 6 h.",
                )
            )
        if w.sport == Sport.RUN and w.purpose_tag.value == "vo2":
            violations.append(
                _violation("INT-047", f"{w.title} uses VO2 — IM run quality must stay sub-VO2.")
            )
        if sem.is_long_ride(w) and w.purpose_tag.value in ("threshold", "vo2"):
            violations.append(
                _violation("RIDE-022", f"{w.title} includes non-aerobic work.")
            )
        if sem.is_long_run(w) and w.purpose_tag.value in ("threshold", "vo2"):
            violations.append(
                _violation("RUN-032", f"{w.title} is not easy aerobic.")
            )
        if sem.is_brick(w) and sem.is_race_sim_brick(w):
            # BRK-039: cap run portion — whole brick duration minus ride estimate is approximate
            if sem.duration_seconds(w) > sem.PEAK_SIM_RIDE_MIN_SECONDS + sem.BRICK_RUN_MAX_OFF_LONG_RIDE:
                violations.append(
                    _violation(
                        "BRK-039",
                        f"{w.title} brick run portion exceeds 90 min off long ride.",
                    )
                )
        if sem.is_long_ride(w) and not w.fueling_notes:
            violations.append(
                _violation("RIDE-028", f"{w.title} missing race fueling rehearsal notes.")
            )

    # --- Rest day — SCH-018 ---
    rest_days = sum(1 for day_workouts in by_day.values() if sem.is_rest_day(day_workouts))
    if rest_days < 1:
        violations.append(_violation("SCH-018", "Week has no full rest day."))

    # --- Run count — RUN-033 ---
    if week.phase != PhaseName.TAPER:
        run_count = sum(1 for w in workouts if w.sport == Sport.RUN)
        if run_count < 2 or run_count > 3:
            violations.append(
                _violation("RUN-033", f"Week has {run_count} run sessions; require 2–3.")
            )

    # --- Long ride anchor — RIDE-021 ---
    long_rides = [w for w in workouts if sem.is_long_ride(w)]
    bricks = [w for w in workouts if sem.is_brick(w)]
    if week.phase not in (PhaseName.TAPER,) and not long_rides and not any(
        sem.is_race_sim_brick(b) for b in bricks
    ):
        violations.append(_violation("RIDE-021", "Week missing long ride anchor."))

    # --- Brick count — SCH-010 ---
    if len(bricks) > sem.MAX_BRICKS_PER_WEEK:
        violations.append(
            _violation("SCH-010", f"Week has {len(bricks)} bricks; max {sem.MAX_BRICKS_PER_WEEK}.")
        )

    # --- Brick spacing — SCH-008, SCH-009 ---
    brick_days = sorted(w.day_of_week for w in bricks if w.day_of_week is not None)
    for i in range(len(brick_days) - 1):
        gap = sem.calendar_day_gap(brick_days[i], brick_days[i + 1])
        if gap < sem.MIN_DAYS_BETWEEN_BRICKS:
            violations.append(
                _violation(
                    "SCH-009",
                    f"Bricks on day {brick_days[i]} and {brick_days[i + 1]} are only {gap} day(s) apart.",
                )
            )
        if gap == 1:
            violations.append(
                _violation("SCH-008", "High-load bricks on consecutive days.")
            )

    # --- Same-day long ride + long run — SCH-004 ---
    for day, day_workouts in by_day.items():
        if any(sem.is_long_ride(w) for w in day_workouts) and any(
            sem.is_long_run(w) for w in day_workouts
        ):
            violations.append(
                _violation(
                    "SCH-004",
                    f"Long ride and long run both scheduled on day {day}.",
                )
            )

    # --- Long bike / long run spacing — SCH-005, SCH-019 ---
    for lr in long_rides:
        for run in (w for w in workouts if sem.is_long_run(w)):
            if lr.day_of_week is None or run.day_of_week is None:
                continue
            gap = min(
                sem.calendar_day_gap(lr.day_of_week, run.day_of_week),
                sem.calendar_day_gap(run.day_of_week, lr.day_of_week),
            )
            if gap < sem.MIN_DAYS_LONG_BIKE_AND_LONG_RUN:
                violations.append(
                    _violation(
                        "SCH-005",
                        f"Long ride (day {lr.day_of_week}) and long run (day {run.day_of_week}) "
                        f"only {gap} day(s) apart; need ≥{sem.MIN_DAYS_LONG_BIKE_AND_LONG_RUN}.",
                    )
                )
            if (
                gap == 1
                and sem.duration_seconds(lr) >= 4 * 3600
                and sem.duration_seconds(run) >= 2 * 3600
            ):
                violations.append(
                    _violation(
                        "SCH-019",
                        "4 h+ ride paired with 2 h+ run on consecutive days.",
                    )
                )

    # --- Hard same discipline 48h — SCH-001 ---
    for sport in (Sport.RUN, Sport.BIKE, Sport.SWIM):
        hard = [
            w
            for w in workouts
            if w.sport == sport and w.is_key_session and sem.is_hard_session(w)
        ]
        for i, a in enumerate(hard):
            for b in hard[i + 1 :]:
                if a.day_of_week is None or b.day_of_week is None:
                    continue
                gap = min(
                    sem.calendar_day_gap(a.day_of_week, b.day_of_week),
                    sem.calendar_day_gap(b.day_of_week, a.day_of_week),
                )
                if gap < sem.MIN_DAYS_HARD_SAME_DISCIPLINE:
                    violations.append(
                        _violation(
                            "SCH-001",
                            f"Hard {sport.value} sessions on days {a.day_of_week} and "
                            f"{b.day_of_week} are only {gap} day(s) apart.",
                        )
                    )

    # --- Demanding 24h — SCH-003 ---
    demanding = [w for w in workouts if sem.is_demanding_session(w)]
    for i, a in enumerate(demanding):
        for b in demanding[i + 1 :]:
            if a.day_of_week is None or b.day_of_week is None:
                continue
            if a.day_of_week == b.day_of_week:
                continue
            gap = min(
                sem.calendar_day_gap(a.day_of_week, b.day_of_week),
                sem.calendar_day_gap(b.day_of_week, a.day_of_week),
            )
            if gap < sem.MIN_DAYS_DEMANDING:
                violations.append(
                    _violation(
                        "SCH-003",
                        f"Demanding sessions on consecutive days ({a.title}, {b.title}).",
                    )
                )

    # --- Hard run after long ride — SCH-006, SCH-007 ---
    for ride in long_rides:
        if ride.day_of_week is None:
            continue
        next_day = (ride.day_of_week + 1) % 7
        for w in by_day.get(next_day, []):
            if w.sport == Sport.RUN and w.is_key_session:
                violations.append(
                    _violation(
                        "SCH-006",
                        f"Key run {w.title} scheduled day after long ride.",
                    )
                )
        # Protect Mon–Tue after Sun long run / Sat-Sun block
        if ride.day_of_week in (5, 6):
            for protect_day in (0, 1):
                for w in by_day.get(protect_day, []):
                    if w.sport == Sport.RUN and w.is_key_session and sem.is_hard_session(w):
                        violations.append(
                            _violation(
                                "SCH-007",
                                f"Hard run {w.title} on day {protect_day} too soon after weekend block.",
                            )
                        )

    # --- Key run 48h after hardest ride — SCH-002 ---
    anchor = _hardest_ride_or_brick(workouts)
    key_runs = [
        w
        for w in workouts
        if w.sport == Sport.RUN
        and w.is_key_session
        and w.purpose_tag.value in ("threshold", "race_execution")
    ]
    if anchor and anchor.day_of_week is not None:
        for kr in key_runs:
            if kr.day_of_week is None:
                continue
            gap = sem.calendar_day_gap(anchor.day_of_week, kr.day_of_week)
            if gap < sem.MIN_DAYS_KEY_RUN_AFTER_HARDEST_RIDE:
                violations.append(
                    _violation(
                        "SCH-002",
                        f"Key run {kr.title} only {gap} day(s) after hardest ride/brick.",
                    )
                )

    # --- Hard bike before long ride — SCH-012 ---
    if long_rides:
        lr_day = long_rides[0].day_of_week
        if lr_day is not None:
            for w in workouts:
                if (
                    w.sport == Sport.BIKE
                    and w.is_key_session
                    and w.purpose_tag.value in ("threshold", "vo2")
                    and w.day_of_week is not None
                ):
                    gap = sem.calendar_day_gap(w.day_of_week, lr_day)
                    if 0 < gap < sem.MIN_DAYS_HARD_BIKE_BEFORE_LONG_RIDE:
                        violations.append(
                            _violation(
                                "SCH-012",
                                f"Hard bike {w.title} only {gap} day(s) before long ride.",
                            )
                        )

    # --- Race-sim brick before key long run — SCH-011 ---
    long_run = _hardest_run(workouts)
    for brick in (b for b in bricks if sem.is_race_sim_brick(b)):
        if brick.day_of_week is None or not long_run or long_run.day_of_week is None:
            continue
        gap = sem.calendar_day_gap(brick.day_of_week, long_run.day_of_week)
        if 0 < gap < sem.MIN_DAYS_LONG_BIKE_AND_LONG_RUN:
            violations.append(
                _violation(
                    "SCH-011",
                    f"Race-sim brick {gap} day(s) before key long run.",
                )
            )

    # --- One key anchor per day — SCH-014 ---
    for day, day_workouts in by_day.items():
        anchors = [
            w
            for w in day_workouts
            if sem.is_long_ride(w)
            or sem.is_long_run(w)
            or sem.is_race_sim_brick(w)
            or (w.is_key_session and sem.is_hard_session(w))
        ]
        transitions = [w for w in day_workouts if sem.is_transition_run(w)]
        if len(anchors) > 1:
            violations.append(
                _violation("SCH-014", f"Day {day} has {len(anchors)} key anchors.")
            )
        if len(anchors) == 1 and transitions and not sem.is_long_ride(anchors[0]):
            violations.append(
                _violation("SCH-014", f"Day {day} stacks anchor with transition run.")
            )

    # --- Three demanding days in a row — SCH-013 ---
    for start in range(7):
        streak = 0
        for offset in range(7):
            day = (start + offset) % 7
            if any(sem.is_demanding_session(w) for w in by_day[day]):
                streak += 1
                if streak >= 3:
                    violations.append(
                        _violation("SCH-013", f"Three demanding days in a row ending day {day}.")
                    )
                    break
            else:
                streak = 0

    # --- One quality per discipline — SCH-015 ---
    if week.phase in (PhaseName.BUILD, PhaseName.PEAK):
        for sport in (Sport.SWIM, Sport.BIKE, Sport.RUN):
            quality = [w for w in workouts if w.sport == sport and sem.is_quality_session(w)]
            if len(quality) > 1:
                violations.append(
                    _violation(
                        "SCH-015",
                        f"{len(quality)} primary quality {sport.value} sessions this week.",
                    )
                )

    # --- Strength vs key run — SCH-020 ---
    if long_run and long_run.day_of_week is not None:
        for check_day in (long_run.day_of_week, (long_run.day_of_week - 1) % 7):
            for w in by_day.get(check_day, []):
                if w.sport == Sport.STRENGTH:
                    violations.append(
                        _violation(
                            "SCH-020",
                            f"Strength on day {check_day} conflicts with long run day {long_run.day_of_week}.",
                        )
                    )

    # --- Brick weekend replaces split — BRK-041 ---
    sim_bricks = [b for b in bricks if sem.is_race_sim_brick(b)]
    if sim_bricks and long_rides and long_run:
        violations.append(
            _violation(
                "BRK-041",
                "Race-sim brick week also has separate long ride and long run.",
            )
        )

    # --- 80/20 — INT-043, INT-044 ---
    easy_frac = sem.easy_time_fraction(workouts)
    if week.target_hours > sem.RECOMMENDED_8020_WEEKLY_HOURS and easy_frac < sem.EASY_INTENSITY_MIN_FRACTION:
        rule = "INT-044" if week.target_hours > sem.MANDATORY_8020_WEEKLY_HOURS else "INT-043"
        violations.append(
            _violation(
                rule,
                f"Easy time {easy_frac:.0%} below 80% at {week.target_hours} h/week.",
            )
        )

    # --- Grey zone — INT-045 ---
    for w in workouts:
        if (
            not w.is_key_session
            and w.purpose_tag.value in ("threshold", "vo2", "durability")
        ):
            violations.append(
                _violation("INT-045", f"Supporting session {w.title} tagged as hard purpose.")
            )
        if sem.is_long_ride(w) and w.purpose_tag.value in ("threshold", "vo2"):
            violations.append(
                _violation("RIDE-022", f"{w.title} includes non-aerobic work.")
            )

    # --- Key flag on quality — INT-046 ---
    for w in workouts:
        if w.purpose_tag.value in ("threshold", "vo2", "race_execution") and not w.is_key_session:
            violations.append(
                _violation("INT-046", f"Quality session {w.title} not marked key.")
            )

    # --- Deload — PER-048, PER-049 ---
    if week.is_deload and week.phase != PhaseName.TAPER:
        # Checked at plan level against non-deload reference; week flag is set by periodization
        pass

    # --- Volume split — RIDE-025 (endurance time only; strength is additive) ---
    endurance = [w for w in workouts if w.sport != Sport.STRENGTH]
    total = sum(sem.duration_seconds(w) for w in endurance)
    if total > 0:
        bike_share = sum(
            sem.duration_seconds(w) for w in endurance if w.sport in (Sport.BIKE, Sport.BRICK)
        ) / total
        if not (0.44 <= bike_share <= 0.56):
            violations.append(
                _violation(
                    "RIDE-025",
                    f"Bike share {bike_share:.0%} outside 45–55% band (target 50%).",
                )
            )

    # --- Taper rules ---
    if week.phase == PhaseName.TAPER and weeks_to_race is not None:
        days_to_race = weeks_to_race * 7
        for w in workouts:
            if sem.is_long_run(w) and days_to_race <= sem.TAPER_NO_LONG_RUN_DAYS:
                violations.append(
                    _violation("TAP-052", f"{w.title} inside {sem.TAPER_NO_LONG_RUN_DAYS} days of race.")
                )
            if sem.is_long_ride(w) and days_to_race <= sem.TAPER_NO_LONG_BIKE_DAYS:
                violations.append(
                    _violation("TAP-053", f"{w.title} inside {sem.TAPER_NO_LONG_BIKE_DAYS} days of race.")
                )

    return violations


def validate_plan(plan: TrainingPlan) -> list[RuleViolation]:
    ctx = RuleContext(
        race_date=plan.athlete_race_date,
        total_weeks=plan.total_weeks,
        all_weeks=tuple(plan.weeks),
        big_day_week_numbers=_big_day_weeks(plan),
    )
    violations: list[RuleViolation] = []
    for week in plan.weeks:
        violations.extend(validate_week(week, ctx))

    violations.extend(_validate_macrocycle(plan, ctx))
    violations.extend(_validate_deloads(plan))
    violations.extend(_validate_peak_sim_bricks(plan, ctx))
    violations.extend(_validate_long_run_timing(plan, ctx))
    return violations


def _big_day_weeks(plan: TrainingPlan) -> frozenset[int]:
    numbers = {
        plan.total_weeks - offset + 1
        for offset in sem.BIG_DAY_WEEKS_BEFORE_RACE
        if plan.total_weeks - offset + 1 >= 1
    }
    return frozenset(numbers)


def _validate_macrocycle(plan: TrainingPlan, ctx: RuleContext) -> list[RuleViolation]:
    violations: list[RuleViolation] = []
    built = {w.week_number for w in plan.weeks}
    missing = ctx.big_day_week_numbers - built
    # Only enforce big-day weeks if those weeks are materialized
    for wn in ctx.big_day_week_numbers & built:
        week = next(w for w in plan.weeks if w.week_number == wn)
        has_sim = any(sem.is_race_sim_brick(b) for b in week.workouts if sem.is_brick(b))
        if not has_sim:
            violations.append(
                _violation("RIDE-027", f"Week {wn} is a big-day week but has no simulation brick.")
            )
    return violations


def _validate_deloads(plan: TrainingPlan) -> list[RuleViolation]:
    violations: list[RuleViolation] = []
    by_num = {w.week_number: w for w in plan.weeks}
    for week in plan.weeks:
        if not week.is_deload:
            continue
        prev = by_num.get(week.week_number - 1)
        if prev and week.target_hours > prev.target_hours * sem.DELOAD_VOLUME_FACTOR + 0.5:
            violations.append(
                _violation(
                    "PER-048",
                    f"Week {week.week_number} deload target {week.target_hours}h not ~35% below prior.",
                )
            )
        if prev and len(week.workouts) < len(prev.workouts) - 1:
            violations.append(
                _violation(
                    "PER-049",
                    f"Week {week.week_number} deload dropped session count vs prior week.",
                )
            )
    return violations


def _validate_peak_sim_bricks(plan: TrainingPlan, ctx: RuleContext) -> list[RuleViolation]:
    final_weeks = range(max(1, ctx.total_weeks - 5), ctx.total_weeks + 1)
    count = 0
    for week in plan.weeks:
        if week.week_number in final_weeks:
            count += sum(
                1 for w in week.workouts if sem.is_brick(w) and sem.is_race_sim_brick(w)
            )
    if count > sem.MAX_PEAK_SIM_BRICKS_FINAL_6_WEEKS and any(
        w.week_number in final_weeks for w in plan.weeks
    ):
        return [
            _violation(
                "BRK-042",
                f"{count} peak sim bricks in final 6 weeks; max {sem.MAX_PEAK_SIM_BRICKS_FINAL_6_WEEKS}.",
            )
        ]
    return []


def _validate_long_run_timing(plan: TrainingPlan, ctx: RuleContext) -> list[RuleViolation]:
    long_run_weeks = [
        w.week_number
        for w in plan.weeks
        for wo in w.workouts
        if sem.is_long_run(wo)
    ]
    if not long_run_weeks:
        return []
    peak_week = max(long_run_weeks)
    weeks_before = ctx.total_weeks - peak_week + 1
    if weeks_before < 2 or weeks_before > 4:
        # Only warn if we have the peak week materialized near race
        if peak_week >= ctx.total_weeks - 5:
            return [
                _violation(
                    "RUN-034",
                    f"Longest run at {weeks_before} week(s) before race; expect 2–4.",
                )
            ]
    return []


def assert_plan_valid(plan: TrainingPlan) -> None:
    violations = validate_plan(plan)
    if violations:
        raise RulesetViolationError(violations)
