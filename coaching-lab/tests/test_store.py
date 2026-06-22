"""Tests for api.persistence.store — SQLite-backed persistence layer."""

from __future__ import annotations

import os
import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from engine.models import (
    AthleteProfile,
    ExperienceLevel,
    GoalType,
    Phase,
    PhaseName,
    PlanState,
    PlannedWeek,
    PurposeTag,
    ReadinessResult,
    ReadinessVerdict,
    Sport,
    StrengthPlan,
    TrainingPlan,
    Workout,
    WorkoutCompletion,
    WorkoutStatus,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

@pytest.fixture()
def store(monkeypatch, tmp_path):
    """Create a Store backed by a temp SQLite DB (no Supabase)."""
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_KEY", raising=False)
    db_path = tmp_path / "test.db"
    with patch("api.persistence.store._DB_PATH", db_path):
        from api.persistence.store import Store
        s = Store()
        yield s


def _profile() -> AthleteProfile:
    return AthleteProfile(
        goal_type=GoalType.FINISH,
        race_name="Ironman Test",
        race_date=date(2027, 6, 1),
        weekly_hours=10,
        limiter_discipline=Sport.RUN,
        experience_level=ExperienceLevel.INTERMEDIATE,
        available_days=[0, 1, 2, 3, 4, 5, 6],
        injury_flags=["knee"],
    )


def _readiness() -> ReadinessResult:
    return ReadinessResult(
        verdict=ReadinessVerdict.GREEN,
        weeks_to_race=24,
        rationale="Solid runway",
        adjustments=["Train around knee"],
    )


def _training_plan() -> TrainingPlan:
    return TrainingPlan(
        athlete_race_date=date(2027, 6, 1),
        total_weeks=20,
        plan_start_date=date(2027, 1, 1),
        phases=[Phase(name=PhaseName.BASE, start_week=1, end_week=20, objective="Build")],
        strength_plan=StrengthPlan(
            sessions_per_week=2, session_duration_minutes=30,
            focus="General", rationale="Injury prevention",
        ),
        weeks=[
            PlannedWeek(
                week_number=1,
                phase=PhaseName.BASE,
                target_hours=8.0,
                workouts=[
                    Workout(
                        id="w-run-1",
                        sport=Sport.RUN,
                        title="Easy run",
                        day_of_week=1,
                        purpose_tag=PurposeTag.AEROBIC_BASE,
                        estimated_duration_seconds=3600,
                        status=WorkoutStatus.PLANNED,
                    ),
                    Workout(
                        id="w-bike-1",
                        sport=Sport.BIKE,
                        title="Long ride",
                        day_of_week=5,
                        purpose_tag=PurposeTag.AEROBIC_BASE,
                        is_key_session=True,
                        estimated_duration_seconds=7200,
                        status=WorkoutStatus.PLANNED,
                    ),
                ],
            )
        ],
    )


# ---------------------------------------------------------------------------
# Guest / athlete
# ---------------------------------------------------------------------------

class TestGuestCRUD:
    def test_create_guest(self, store):
        result = store.create_guest()
        assert "id" in result
        assert "guest_id" in result

    def test_create_guest_with_id(self, store):
        result = store.create_guest(guest_id="my-guest-123")
        assert result["guest_id"] == "my-guest-123"

    def test_get_athlete_by_guest(self, store):
        created = store.create_guest(guest_id="g1")
        found = store.get_athlete_by_guest("g1")
        assert found is not None
        assert found["guest_id"] == "g1"
        assert found["id"] == created["id"]

    def test_get_athlete_by_guest_not_found(self, store):
        assert store.get_athlete_by_guest("nonexistent") is None


# ---------------------------------------------------------------------------
# Auth linking
# ---------------------------------------------------------------------------

class TestAuthLinking:
    def test_link_guest_to_auth(self, store):
        created = store.create_guest(guest_id="g2")
        athlete_id = store.link_guest_to_auth("g2", "auth-user-1")
        assert athlete_id == created["id"]
        found = store.get_athlete_by_auth_user("auth-user-1")
        assert found is not None
        assert found["id"] == athlete_id

    def test_link_idempotent(self, store):
        store.create_guest(guest_id="g3")
        aid1 = store.link_guest_to_auth("g3", "auth-user-2")
        aid2 = store.link_guest_to_auth("g3", "auth-user-2")
        assert aid1 == aid2

    def test_link_guest_not_found_raises(self, store):
        with pytest.raises(store.GuestNotFoundError):
            store.link_guest_to_auth("no-such-guest", "auth-1")

    def test_link_conflict_different_athlete(self, store):
        store.create_guest(guest_id="g4")
        store.create_guest(guest_id="g5")
        store.link_guest_to_auth("g4", "auth-shared")
        with pytest.raises(store.AuthLinkConflictError):
            store.link_guest_to_auth("g5", "auth-shared")

    def test_link_conflict_already_linked_different_auth(self, store):
        store.create_guest(guest_id="g6")
        store.link_guest_to_auth("g6", "auth-A")
        with pytest.raises(store.AuthLinkConflictError):
            store.link_guest_to_auth("g6", "auth-B")


# ---------------------------------------------------------------------------
# Profile persistence
# ---------------------------------------------------------------------------

class TestProfilePersistence:
    def test_upsert_and_read_profile(self, store):
        created = store.create_guest(guest_id="gp1")
        aid = created["id"]
        profile = _profile()
        readiness = _readiness()
        store.upsert_athlete_profile(aid, profile, readiness)
        row = store.get_athlete_by_guest("gp1")
        assert row is not None

        loaded = store.profile_from_row(row)
        assert loaded is not None
        assert loaded.race_name == "Ironman Test"
        assert loaded.experience_level == ExperienceLevel.INTERMEDIATE
        assert loaded.injury_flags == ["knee"]
        assert loaded.weekly_hours == 10

    def test_readiness_from_row(self, store):
        created = store.create_guest(guest_id="gp2")
        aid = created["id"]
        store.upsert_athlete_profile(aid, _profile(), _readiness())
        row = store.get_athlete_by_guest("gp2")
        r = store.readiness_from_row(row)
        assert r is not None
        assert r.verdict == ReadinessVerdict.GREEN
        assert r.weeks_to_race == 24
        assert "Train around knee" in r.adjustments

    def test_profile_from_row_no_race_date(self, store):
        created = store.create_guest(guest_id="gp3")
        row = store.get_athlete_by_guest("gp3")
        assert store.profile_from_row(row) is None

    def test_readiness_from_row_no_verdict(self, store):
        created = store.create_guest(guest_id="gp4")
        row = store.get_athlete_by_guest("gp4")
        assert store.readiness_from_row(row) is None


# ---------------------------------------------------------------------------
# Plan persistence
# ---------------------------------------------------------------------------

class TestPlanPersistence:
    def test_save_and_get_plan(self, store):
        created = store.create_guest(guest_id="pp1")
        aid = created["id"]
        plan = _training_plan()
        plan_id = store.save_plan(aid, plan, "Test summary")
        assert plan_id

        current = store.get_current_plan(aid)
        assert current is not None
        assert current["total_weeks"] == 20
        assert len(current["phases"]) == 1

    def test_activate_plan(self, store):
        created = store.create_guest(guest_id="pp2")
        aid = created["id"]
        pid = store.save_plan(aid, _training_plan(), "Summary")
        store.activate_plan(aid, pid)
        current = store.get_current_plan(aid)
        assert current is not None
        assert current["status"] == "active"

    def test_get_current_plan_none(self, store):
        created = store.create_guest(guest_id="pp3")
        assert store.get_current_plan(created["id"]) is None


# ---------------------------------------------------------------------------
# Workout operations
# ---------------------------------------------------------------------------

class TestWorkoutOperations:
    def test_list_workouts(self, store):
        created = store.create_guest(guest_id="wo1")
        aid = created["id"]
        store.save_plan(aid, _training_plan(), "S")
        workouts = store.list_workouts(aid)
        assert len(workouts) == 2
        assert workouts[0]["sport"] in ("run", "bike")

    def test_list_workouts_filter_sport(self, store):
        created = store.create_guest(guest_id="wo2")
        aid = created["id"]
        store.save_plan(aid, _training_plan(), "S")
        runs = store.list_workouts(aid, sport="run")
        assert all(w["sport"] == "run" for w in runs)

    def test_get_workout(self, store):
        created = store.create_guest(guest_id="wo3")
        aid = created["id"]
        store.save_plan(aid, _training_plan(), "S")
        workouts = store.list_workouts(aid)
        first = workouts[0]
        fetched = store.get_workout(first["id"], aid)
        assert fetched is not None
        assert fetched["title"] == first["title"]

    def test_get_workout_not_found(self, store):
        created = store.create_guest(guest_id="wo4")
        assert store.get_workout("fake-id", created["id"]) is None

    def test_complete_workout(self, store):
        created = store.create_guest(guest_id="wo5")
        aid = created["id"]
        store.save_plan(aid, _training_plan(), "S")
        workouts = store.list_workouts(aid)
        wid = workouts[0]["id"]
        completion = WorkoutCompletion(
            workout_id=wid,
            sport=Sport.RUN,
            completed=True,
            rpe=7,
            readiness_score=8,
        )
        result = store.complete_workout(wid, aid, completion)
        assert result["status"] == "completed"

        updated = store.get_workout(wid, aid)
        assert updated["status"] == "completed"

    def test_complete_workout_skipped(self, store):
        created = store.create_guest(guest_id="wo6")
        aid = created["id"]
        store.save_plan(aid, _training_plan(), "S")
        workouts = store.list_workouts(aid)
        wid = workouts[0]["id"]
        completion = WorkoutCompletion(
            workout_id=wid, sport=Sport.RUN, completed=False,
        )
        result = store.complete_workout(wid, aid, completion)
        assert result["status"] == "skipped"

    def test_list_completions(self, store):
        created = store.create_guest(guest_id="wo7")
        aid = created["id"]
        store.save_plan(aid, _training_plan(), "S")
        workouts = store.list_workouts(aid)
        wid = workouts[0]["id"]
        store.complete_workout(
            wid, aid,
            WorkoutCompletion(workout_id=wid, sport=Sport.RUN, completed=True, rpe=6),
        )
        comps = store.list_completions(aid)
        assert len(comps) == 1
        assert comps[0]["completed"]

    def test_completions_for_adaptation(self, store):
        created = store.create_guest(guest_id="wo8")
        aid = created["id"]
        store.save_plan(aid, _training_plan(), "S")
        workouts = store.list_workouts(aid)
        wid = workouts[0]["id"]
        store.complete_workout(
            wid, aid,
            WorkoutCompletion(
                workout_id=wid, sport=Sport.RUN, completed=True, rpe=7,
                fatigue_flags=["tired legs"],
            ),
        )
        adapt = store.completions_for_adaptation(aid)
        assert len(adapt) == 1
        assert adapt[0].rpe == 7
        assert "tired legs" in adapt[0].fatigue_flags


# ---------------------------------------------------------------------------
# Plan state
# ---------------------------------------------------------------------------

class TestPlanState:
    def test_get_and_set_plan_state(self, store):
        created = store.create_guest(guest_id="ps1")
        aid = created["id"]
        pid = store.save_plan(aid, _training_plan(), "S")
        state = store.get_plan_state(pid)
        assert state.volume_multiplier == 1.0

        state.volume_multiplier = 0.9
        state.consecutive_holds = 2
        store.save_plan_state(pid, state)

        reloaded = store.get_plan_state(pid)
        assert reloaded.volume_multiplier == 0.9
        assert reloaded.consecutive_holds == 2
