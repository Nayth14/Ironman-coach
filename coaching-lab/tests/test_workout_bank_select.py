from __future__ import annotations

from engine.models import (
    PhaseName,
    PlanState,
    PlannedWeek,
    PurposeTag,
    Sport,
    Workout,
    WorkoutStatus,
)
from engine.workout_bank.assign import SwimBankAssignmentError, assign_bank_workouts
import pytest

def _wk(workouts: list[Workout], *, phase: PhaseName = PhaseName.BASE, is_deload: bool = False) -> PlannedWeek:
    return PlannedWeek(
        week_number=2,
        phase=phase,
        is_deload=is_deload,
        target_hours=10.0,
        workouts=workouts,
    )


def _wo(
    wid: str,
    sport: Sport,
    title: str,
    purpose: PurposeTag,
    *,
    key: bool,
    seconds: int,
) -> Workout:
    return Workout(
        id=wid,
        sport=sport,
        title=title,
        purpose_tag=purpose,
        is_key_session=key,
        estimated_duration_seconds=seconds,
        status=WorkoutStatus.PLANNED,
    )


def test_assign_base_keeps_easy_filler_unbanked():
    week = _wk(
        [
            _wo("bike-long", Sport.BIKE, "Long ride", PurposeTag.AEROBIC_BASE, key=True, seconds=3 * 3600),
            _wo("bike-hard", Sport.BIKE, "Bike sweet spot", PurposeTag.THRESHOLD, key=True, seconds=60 * 60),
            _wo("run-long", Sport.RUN, "Long run", PurposeTag.AEROBIC_BASE, key=True, seconds=120 * 60),
            _wo("run-hard", Sport.RUN, "Run tempo", PurposeTag.THRESHOLD, key=True, seconds=60 * 60),
            _wo("run-easy", Sport.RUN, "Easy run", PurposeTag.AEROBIC_BASE, key=False, seconds=40 * 60),
        ]
    )
    state = PlanState()
    out = assign_bank_workouts(week, phase=PhaseName.BASE, state=state)
    by_id = {w.id: w for w in out.workouts}

    assert by_id["bike-hard"].bank_workout_id and by_id["bike-hard"].bank_workout_id.startswith("SS")
    assert by_id["run-hard"].bank_workout_id and by_id["run-hard"].bank_workout_id.startswith("TMP")
    assert by_id["run-long"].bank_workout_id and by_id["run-long"].bank_workout_id.endswith("-1")
    assert by_id["run-easy"].bank_workout_id is None


def test_assign_deload_skips_hard_intervals_but_keeps_long_run():
    week = _wk(
        [
            _wo("run-hard", Sport.RUN, "Run threshold", PurposeTag.THRESHOLD, key=True, seconds=60 * 60),
            _wo("run-long", Sport.RUN, "Long run", PurposeTag.AEROBIC_BASE, key=True, seconds=150 * 60),
        ],
        phase=PhaseName.BUILD,
        is_deload=True,
    )
    state = PlanState()
    out = assign_bank_workouts(week, phase=PhaseName.BUILD, state=state)
    by_id = {w.id: w for w in out.workouts}

    assert by_id["run-hard"].bank_workout_id is None
    assert by_id["run-long"].bank_workout_id and by_id["run-long"].bank_workout_id.endswith("-1")


def test_assign_all_swim_sessions_from_bank():
    week = _wk(
        [
            _wo("swim-tech", Sport.SWIM, "Swim technique", PurposeTag.ECONOMY, key=True, seconds=60 * 60),
            _wo("swim-endurance", Sport.SWIM, "Swim endurance", PurposeTag.AEROBIC_BASE, key=False, seconds=50 * 60),
        ]
    )
    state = PlanState()
    out = assign_bank_workouts(week, phase=PhaseName.BASE, state=state)
    by_id = {w.id: w for w in out.workouts}

    assert by_id["swim-tech"].bank_workout_id and by_id["swim-tech"].bank_workout_id.startswith("TECH")
    assert by_id["swim-endurance"].bank_workout_id and by_id["swim-endurance"].bank_workout_id.startswith("AER")
    assert by_id["swim-tech"].description
    assert by_id["swim-endurance"].description


def test_assign_deload_swim_uses_technique_or_aerobic_only():
    week = _wk(
        [
            _wo("swim-tech", Sport.SWIM, "Swim technique", PurposeTag.ECONOMY, key=True, seconds=45 * 60),
            _wo("swim-endurance", Sport.SWIM, "Swim endurance", PurposeTag.AEROBIC_BASE, key=False, seconds=45 * 60),
        ],
        phase=PhaseName.BUILD,
        is_deload=True,
    )
    state = PlanState()
    out = assign_bank_workouts(week, phase=PhaseName.BUILD, state=state)
    by_id = {w.id: w for w in out.workouts}

    for wid in ("swim-tech", "swim-endurance"):
        bank_id = by_id[wid].bank_workout_id
        assert bank_id
        assert bank_id.startswith("TECH") or bank_id.startswith("AER")


def test_assign_swim_raises_when_no_bank_match(monkeypatch):
    def _no_match(*_args, **_kwargs):
        return None

    monkeypatch.setattr(
        "engine.workout_bank.assign.pick_bank_workout",
        _no_match,
    )
    week = _wk(
        [
            _wo("swim-bad", Sport.SWIM, "Swim technique", PurposeTag.ECONOMY, key=True, seconds=60 * 60),
        ]
    )
    state = PlanState()
    with pytest.raises(SwimBankAssignmentError):
        assign_bank_workouts(week, phase=PhaseName.BASE, state=state)
