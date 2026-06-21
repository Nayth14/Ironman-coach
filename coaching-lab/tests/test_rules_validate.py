from __future__ import annotations

from datetime import date

from engine.models import PhaseName, PlannedWeek, PurposeTag, Sport, Workout, WorkoutStatus
from engine.rules.validate import RuleContext, validate_week


def _w(wid: str, day: int, sport: Sport, purpose: PurposeTag, title: str) -> Workout:
    return Workout(
        id=wid,
        sport=sport,
        title=title,
        day_of_week=day,
        purpose_tag=purpose,
        is_key_session=True,
        estimated_duration_seconds=60 * 60,
        status=WorkoutStatus.PLANNED,
    )


def test_sch_013_not_duplicated_for_same_ending_day():
    week = PlannedWeek(
        week_number=1,
        phase=PhaseName.PREP,
        target_hours=8.0,
        workouts=[
            _w("run1", 1, Sport.RUN, PurposeTag.THRESHOLD, "Run threshold"),
            _w("bike1", 2, Sport.BIKE, PurposeTag.THRESHOLD, "Bike threshold"),
            _w("swim1", 3, Sport.SWIM, PurposeTag.THRESHOLD, "Swim threshold"),
        ],
    )
    violations = validate_week(week, RuleContext(race_date=date(2027, 1, 1), total_weeks=16))
    sch_013_msgs = [v.message for v in violations if v.rule_id == "SCH-013"]
    assert sch_013_msgs
    assert len(sch_013_msgs) == len(set(sch_013_msgs))
