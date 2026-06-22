"""Tests for engine.rules.validate — training plan rule enforcement."""

from __future__ import annotations

from datetime import date

import pytest

from engine.models import (
    Phase,
    PhaseName,
    PlannedWeek,
    PurposeTag,
    Sport,
    StrengthPlan,
    TrainingPlan,
    Workout,
    WorkoutStatus,
)
from engine.rules.validate import (
    RuleContext,
    RuleViolation,
    RulesetViolationError,
    assert_plan_valid,
    validate_plan,
    validate_week,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _w(
    *,
    id: str = "w1",
    sport: Sport = Sport.RUN,
    title: str = "Workout",
    purpose_tag: PurposeTag = PurposeTag.AEROBIC_BASE,
    is_key: bool = False,
    duration: int = 3600,
    day: int = 0,
    distance: float | None = None,
    fueling_notes: str | None = None,
) -> Workout:
    return Workout(
        id=id, sport=sport, title=title,
        purpose_tag=purpose_tag, is_key_session=is_key,
        estimated_duration_seconds=duration,
        estimated_distance_meters=distance,
        day_of_week=day, status=WorkoutStatus.PLANNED,
        fueling_notes=fueling_notes,
    )


def _week(
    workouts: list[Workout],
    *,
    week_number: int = 1,
    phase: PhaseName = PhaseName.BASE,
    target_hours: float = 8.0,
    is_deload: bool = False,
) -> PlannedWeek:
    return PlannedWeek(
        week_number=week_number,
        phase=phase,
        is_deload=is_deload,
        target_hours=target_hours,
        workouts=workouts,
    )


def _ctx(total_weeks: int = 20) -> RuleContext:
    return RuleContext(
        race_date=date(2027, 6, 1),
        total_weeks=total_weeks,
    )


def _plan(weeks: list[PlannedWeek], total_weeks: int = 20) -> TrainingPlan:
    return TrainingPlan(
        athlete_race_date=date(2027, 6, 1),
        total_weeks=total_weeks,
        plan_start_date=date(2027, 1, 1),
        phases=[Phase(name=PhaseName.BASE, start_week=1, end_week=total_weeks, objective="Base")],
        strength_plan=StrengthPlan(
            sessions_per_week=2, session_duration_minutes=30,
            focus="General", rationale="Prevent injury",
        ),
        weeks=weeks,
    )


def _rule_ids(violations: list[RuleViolation]) -> set[str]:
    return {v.rule_id for v in violations}


# ---------------------------------------------------------------------------
# A valid baseline week (no violations expected)
# ---------------------------------------------------------------------------

def _valid_base_week() -> PlannedWeek:
    """Minimal week that should pass all weekly rules."""
    return _week([
        _w(id="swim1", sport=Sport.SWIM, title="Swim technique", duration=3600, day=1),
        _w(id="bike1", sport=Sport.BIKE, title="Long ride", duration=4 * 3600,
           is_key=True, fueling_notes="60 g/h carbs", day=5),
        _w(id="run1", sport=Sport.RUN, title="Easy run", duration=3000, day=2),
        _w(id="run2", sport=Sport.RUN, title="Tempo run", duration=3600, day=4,
           is_key=True, purpose_tag=PurposeTag.THRESHOLD),
        # Day 0 (Mon) and 6 (Sun) are rest days
    ])


# ---------------------------------------------------------------------------
# RUN-030: Long run cap 150 min
# ---------------------------------------------------------------------------

class TestRunCaps:
    def test_long_run_over_150_min(self):
        w = _w(id="lr", sport=Sport.RUN, title="Long run",
               purpose_tag=PurposeTag.AEROBIC_BASE, is_key=True,
               duration=160 * 60, day=0)  # 160 min > 150
        violations = validate_week(_week([w]))
        assert "RUN-030" in _rule_ids(violations)

    def test_long_run_at_150_min_ok(self):
        w = _w(id="lr", sport=Sport.RUN, title="Long run",
               purpose_tag=PurposeTag.AEROBIC_BASE, is_key=True,
               duration=150 * 60, day=0)
        violations = validate_week(_week([w]))
        assert "RUN-030" not in _rule_ids(violations)

    def test_run_marathon_distance(self):
        w = _w(id="mr", sport=Sport.RUN, title="Marathon dist",
               duration=3 * 3600, day=0, distance=42200)
        violations = validate_week(_week([w]))
        assert "RUN-031" in _rule_ids(violations)


# ---------------------------------------------------------------------------
# INT-047: VO2 run forbidden
# ---------------------------------------------------------------------------

class TestVO2Run:
    def test_vo2_run_flagged(self):
        w = _w(id="v2", sport=Sport.RUN, title="VO2 Run",
               purpose_tag=PurposeTag.VO2, is_key=True, day=0)
        violations = validate_week(_week([w]))
        assert "INT-047" in _rule_ids(violations)

    def test_threshold_run_ok(self):
        w = _w(id="tr", sport=Sport.RUN, title="Tempo run",
               purpose_tag=PurposeTag.THRESHOLD, is_key=True, day=0)
        violations = validate_week(_week([w]))
        assert "INT-047" not in _rule_ids(violations)


# ---------------------------------------------------------------------------
# RIDE-022: Long ride must be aerobic
# ---------------------------------------------------------------------------

class TestLongRideAerobic:
    def test_long_ride_threshold_flagged(self):
        w = _w(id="lr", sport=Sport.BIKE, title="Long ride",
               purpose_tag=PurposeTag.THRESHOLD, is_key=True,
               duration=4 * 3600, day=5, fueling_notes="fuel")
        violations = validate_week(_week([w]))
        assert "RIDE-022" in _rule_ids(violations)


# ---------------------------------------------------------------------------
# RIDE-028: Long ride needs fueling notes
# ---------------------------------------------------------------------------

class TestFuelingNotes:
    def test_long_ride_missing_fueling(self):
        w = _w(id="lr", sport=Sport.BIKE, title="Long ride",
               purpose_tag=PurposeTag.AEROBIC_BASE, is_key=True,
               duration=4 * 3600, day=5)
        violations = validate_week(_week([w]))
        assert "RIDE-028" in _rule_ids(violations)

    def test_long_ride_with_fueling_ok(self):
        w = _w(id="lr", sport=Sport.BIKE, title="Long ride",
               purpose_tag=PurposeTag.AEROBIC_BASE, is_key=True,
               duration=4 * 3600, day=5, fueling_notes="60 g/h carbs")
        violations = validate_week(_week([w]))
        assert "RIDE-028" not in _rule_ids(violations)


# ---------------------------------------------------------------------------
# SCH-018: At least one rest day
# ---------------------------------------------------------------------------

class TestRestDay:
    def test_no_rest_day_flagged(self):
        workouts = [
            _w(id=f"w{d}", day=d, duration=3600) for d in range(7)
        ]
        violations = validate_week(_week(workouts))
        assert "SCH-018" in _rule_ids(violations)


# ---------------------------------------------------------------------------
# RUN-033: 2-3 runs per week (non-taper)
# ---------------------------------------------------------------------------

class TestRunCount:
    def test_one_run_flagged(self):
        workouts = [_w(id="r1", sport=Sport.RUN, day=0)]
        violations = validate_week(_week(workouts))
        assert "RUN-033" in _rule_ids(violations)

    def test_four_runs_flagged(self):
        workouts = [_w(id=f"r{i}", sport=Sport.RUN, day=i) for i in range(4)]
        violations = validate_week(_week(workouts))
        assert "RUN-033" in _rule_ids(violations)

    def test_taper_exempt(self):
        workouts = [_w(id="r1", sport=Sport.RUN, day=0)]
        violations = validate_week(_week(workouts, phase=PhaseName.TAPER))
        assert "RUN-033" not in _rule_ids(violations)


# ---------------------------------------------------------------------------
# RIDE-021: Long ride anchor required (non-taper)
# ---------------------------------------------------------------------------

class TestLongRideAnchor:
    def test_no_long_ride_flagged(self):
        workouts = [
            _w(id="b1", sport=Sport.BIKE, title="Short ride", duration=2 * 3600, day=5),
        ]
        violations = validate_week(_week(workouts))
        assert "RIDE-021" in _rule_ids(violations)

    def test_taper_exempt(self):
        workouts = [
            _w(id="b1", sport=Sport.BIKE, title="Short ride", duration=2 * 3600, day=5),
        ]
        violations = validate_week(_week(workouts, phase=PhaseName.TAPER))
        assert "RIDE-021" not in _rule_ids(violations)


# ---------------------------------------------------------------------------
# INT-045: Grey zone — non-key hard purpose
# ---------------------------------------------------------------------------

class TestGreyZone:
    def test_non_key_threshold_flagged(self):
        w = _w(id="gz", purpose_tag=PurposeTag.THRESHOLD, is_key=False, day=0)
        violations = validate_week(_week([w]))
        assert "INT-045" in _rule_ids(violations)

    def test_key_threshold_ok(self):
        w = _w(id="ok", purpose_tag=PurposeTag.THRESHOLD, is_key=True, day=0)
        violations = validate_week(_week([w]))
        assert "INT-045" not in _rule_ids(violations)


# ---------------------------------------------------------------------------
# INT-046: Quality session must be marked key
# ---------------------------------------------------------------------------

class TestKeyFlag:
    def test_quality_not_key_flagged(self):
        w = _w(id="q1", purpose_tag=PurposeTag.RACE_EXECUTION, is_key=False, day=0)
        violations = validate_week(_week([w]))
        assert "INT-046" in _rule_ids(violations)


# ---------------------------------------------------------------------------
# SCH-004: Same-day long ride + long run
# ---------------------------------------------------------------------------

class TestSameDayLongSessions:
    def test_long_ride_and_long_run_same_day(self):
        ride = _w(id="lr", sport=Sport.BIKE, title="Long ride",
                  duration=4 * 3600, is_key=True, day=5, fueling_notes="fuel")
        run = _w(id="lrun", sport=Sport.RUN, title="Long run",
                 duration=100 * 60, is_key=True, day=5)
        violations = validate_week(_week([ride, run]))
        assert "SCH-004" in _rule_ids(violations)


# ---------------------------------------------------------------------------
# SCH-013: Three demanding days in a row
# ---------------------------------------------------------------------------

class TestThreeDemandingDays:
    def test_three_consecutive(self):
        workouts = [
            _w(id="d1", sport=Sport.BIKE, title="Hard ride",
               purpose_tag=PurposeTag.THRESHOLD, is_key=True, duration=4 * 3600, day=1,
               fueling_notes="fuel"),
            _w(id="d2", sport=Sport.RUN, title="Tempo",
               purpose_tag=PurposeTag.THRESHOLD, is_key=True, duration=3600, day=2),
            _w(id="d3", sport=Sport.BIKE, title="Long ride",
               purpose_tag=PurposeTag.AEROBIC_BASE, is_key=True, duration=4 * 3600, day=3,
               fueling_notes="fuel"),
        ]
        violations = validate_week(_week(workouts))
        assert "SCH-013" in _rule_ids(violations)


# ---------------------------------------------------------------------------
# validate_plan — plan-level checks
# ---------------------------------------------------------------------------

class TestValidatePlan:
    def test_deload_too_high_volume(self):
        w1 = _week(
            [_w(id="b1", sport=Sport.BIKE, duration=4 * 3600, day=5,
                fueling_notes="fuel", is_key=True, title="Long ride")],
            week_number=1, target_hours=10.0,
        )
        w2 = _week(
            [_w(id="b2", sport=Sport.BIKE, duration=4 * 3600, day=5,
                fueling_notes="fuel", is_key=True, title="Long ride")],
            week_number=2, target_hours=9.0, is_deload=True,
        )
        violations = validate_plan(_plan([w1, w2]))
        assert "PER-048" in _rule_ids(violations)

    def test_deload_proper_volume_ok(self):
        w1 = _week(
            [_w(id="b1", sport=Sport.BIKE, duration=4 * 3600, day=5,
                fueling_notes="fuel", is_key=True, title="Long ride")],
            week_number=1, target_hours=10.0,
        )
        w2 = _week(
            [_w(id="b2", sport=Sport.BIKE, duration=2 * 3600, day=5,
                fueling_notes="fuel", is_key=True, title="Ride")],
            week_number=2, target_hours=6.0, is_deload=True,
        )
        violations = validate_plan(_plan([w1, w2]))
        assert "PER-048" not in _rule_ids(violations)


# ---------------------------------------------------------------------------
# RulesetViolationError
# ---------------------------------------------------------------------------

class TestRulesetViolationError:
    def test_error_contains_violations(self):
        v = RuleViolation(rule_id="RUN-030", message="Too long")
        err = RulesetViolationError([v])
        assert err.violations == [v]
        assert "RUN-030" in str(err)

    def test_assert_plan_valid_raises(self):
        w = _week([
            _w(id="lr", sport=Sport.RUN, title="Long run",
               duration=160 * 60, is_key=True, day=0),
        ])
        plan = _plan([w])
        with pytest.raises(RulesetViolationError) as exc_info:
            assert_plan_valid(plan)
        assert len(exc_info.value.violations) > 0
