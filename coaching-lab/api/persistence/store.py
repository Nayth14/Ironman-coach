"""Persistence layer for the Ironman Coach API.

Uses Supabase when SUPABASE_URL + SUPABASE_SERVICE_KEY are set; otherwise
falls back to a local SQLite database so the app runs without cloud setup.
"""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional

from engine.models import (
    AdaptationDecision,
    AdaptationResult,
    AthleteProfile,
    Phase,
    ReadinessResult,
    Sport,
    StrengthPlan,
    TrainingPlan,
    Workout,
    WorkoutCompletion,
    WorkoutStatus,
)

_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "ironman_coach.db"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return str(uuid.uuid4())


class Store:
    """Abstract persistence; SQLite implementation for MVP local dev."""

    def __init__(self) -> None:
        self._use_supabase = bool(
            os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_SERVICE_KEY")
        )
        if self._use_supabase:
            from supabase import create_client

            self._sb = create_client(
                os.environ["SUPABASE_URL"],
                os.environ["SUPABASE_SERVICE_KEY"],
            )
        else:
            _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            self._init_sqlite()

    def _init_sqlite(self) -> None:
        with self._sqlite() as conn:
            conn.executescript(
                (Path(__file__).parent / "schema_sqlite.sql").read_text(encoding="utf-8")
            )
            self._migrate_sqlite(conn)

    def _migrate_sqlite(self, conn: sqlite3.Connection) -> None:
        cols = {
            row[1]
            for row in conn.execute("PRAGMA table_info(training_plans)").fetchall()
        }
        if "plan_start_date" not in cols:
            conn.execute(
                "ALTER TABLE training_plans ADD COLUMN plan_start_date TEXT"
            )

    @contextmanager
    def _sqlite(self):
        conn = sqlite3.connect(_DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Guests / athletes
    # ------------------------------------------------------------------

    def create_guest(self, guest_id: str | None = None) -> dict[str, Any]:
        gid = guest_id or _new_id()
        aid = _new_id()
        if self._use_supabase:
            row = (
                self._sb.table("athletes")
                .insert({"id": aid, "guest_id": gid, "goal_type": "finish"})
                .execute()
            )
            return row.data[0]
        with self._sqlite() as conn:
            conn.execute(
                "INSERT INTO athletes (id, guest_id, goal_type, created_at, updated_at) VALUES (?,?,?,?,?)",
                (aid, gid, "finish", _utcnow(), _utcnow()),
            )
        return {"id": aid, "guest_id": gid}

    def get_athlete_by_guest(self, guest_id: str) -> dict[str, Any] | None:
        if self._use_supabase:
            res = (
                self._sb.table("athletes")
                .select("*")
                .eq("guest_id", guest_id)
                .limit(1)
                .execute()
            )
            return res.data[0] if res.data else None
        with self._sqlite() as conn:
            row = conn.execute(
                "SELECT * FROM athletes WHERE guest_id = ?", (guest_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_athlete_by_auth_user(self, auth_user_id: str) -> dict[str, Any] | None:
        if self._use_supabase:
            res = (
                self._sb.table("athletes")
                .select("*")
                .eq("auth_user_id", auth_user_id)
                .limit(1)
                .execute()
            )
            return res.data[0] if res.data else None
        with self._sqlite() as conn:
            row = conn.execute(
                "SELECT * FROM athletes WHERE auth_user_id = ?", (auth_user_id,)
            ).fetchone()
            return dict(row) if row else None

    class GuestNotFoundError(Exception):
        pass

    class AuthLinkConflictError(Exception):
        pass

    def link_guest_to_auth(self, guest_id: str, auth_user_id: str) -> str:
        """Link guest athlete row to auth user. Returns athlete id."""
        guest_athlete = self.get_athlete_by_guest(guest_id)
        if not guest_athlete:
            raise Store.GuestNotFoundError()

        existing = self.get_athlete_by_auth_user(auth_user_id)
        if existing:
            if existing["id"] == guest_athlete["id"]:
                return str(guest_athlete["id"])
            raise Store.AuthLinkConflictError()

        current_auth = guest_athlete.get("auth_user_id")
        if current_auth:
            if str(current_auth) == auth_user_id:
                return str(guest_athlete["id"])
            raise Store.AuthLinkConflictError()

        athlete_id = str(guest_athlete["id"])
        if self._use_supabase:
            self._sb.table("athletes").update(
                {"auth_user_id": auth_user_id, "updated_at": _utcnow()}
            ).eq("id", athlete_id).execute()
            return athlete_id

        with self._sqlite() as conn:
            conn.execute(
                "UPDATE athletes SET auth_user_id = ?, updated_at = ? WHERE id = ?",
                (auth_user_id, _utcnow(), athlete_id),
            )
        return athlete_id

    def upsert_athlete_profile(
        self,
        athlete_id: str,
        profile: AthleteProfile,
        readiness: ReadinessResult,
    ) -> None:
        data = {
            "goal_type": profile.goal_type.value,
            "race_name": profile.race_name,
            "race_date": profile.race_date.isoformat(),
            "weekly_hours": profile.weekly_hours,
            "limiter_discipline": profile.limiter_discipline.value,
            "experience_level": profile.experience_level.value,
            "available_days": profile.available_days,
            "injury_flags": profile.injury_flags,
            "strength_background": profile.strength_background.value,
            "strength_equipment": profile.strength_equipment.value,
            "current_strength_routine": profile.current_strength_routine,
            "strength_restrictions": profile.strength_restrictions,
            "confidence": profile.confidence,
            "readiness_verdict": readiness.verdict.value,
            "readiness_rationale": readiness.rationale,
            "readiness_adjustments": readiness.adjustments,
            "weeks_to_race": readiness.weeks_to_race,
            "updated_at": _utcnow(),
        }
        if self._use_supabase:
            self._sb.table("athletes").update(data).eq("id", athlete_id).execute()
            return
        with self._sqlite() as conn:
            conn.execute(
                """UPDATE athletes SET
                    goal_type=?, race_name=?, race_date=?, weekly_hours=?,
                    limiter_discipline=?, experience_level=?, available_days=?,
                    injury_flags=?, strength_background=?, strength_equipment=?,
                    current_strength_routine=?, strength_restrictions=?, confidence=?,
                    readiness_verdict=?, readiness_rationale=?, readiness_adjustments=?,
                    weeks_to_race=?, updated_at=?
                WHERE id=?""",
                (
                    data["goal_type"],
                    data["race_name"],
                    data["race_date"],
                    data["weekly_hours"],
                    data["limiter_discipline"],
                    data["experience_level"],
                    json.dumps(data["available_days"]),
                    json.dumps(data["injury_flags"]),
                    data["strength_background"],
                    data["strength_equipment"],
                    data["current_strength_routine"],
                    json.dumps(data["strength_restrictions"]),
                    data["confidence"],
                    data["readiness_verdict"],
                    data["readiness_rationale"],
                    json.dumps(data["readiness_adjustments"]),
                    data["weeks_to_race"],
                    data["updated_at"],
                    athlete_id,
                ),
            )

    def profile_from_row(self, row: dict[str, Any]) -> AthleteProfile | None:
        if not row.get("race_date"):
            return None
        ad = row.get("available_days")
        if isinstance(ad, str):
            ad = json.loads(ad)
        inj = row.get("injury_flags")
        if isinstance(inj, str):
            inj = json.loads(inj)
        sr = row.get("strength_restrictions")
        if isinstance(sr, str):
            sr = json.loads(sr)
        return AthleteProfile(
            goal_type=row["goal_type"],
            race_name=row["race_name"] or "",
            race_date=date.fromisoformat(row["race_date"]),
            weekly_hours=row["weekly_hours"] or 8,
            limiter_discipline=row["limiter_discipline"] or "run",
            experience_level=row["experience_level"] or "intermediate",
            available_days=ad or [0, 1, 2, 3, 4, 5, 6],
            injury_flags=inj or [],
            strength_background=row.get("strength_background") or "none",
            strength_equipment=row.get("strength_equipment") or "minimal",
            current_strength_routine=row.get("current_strength_routine"),
            strength_restrictions=sr or [],
            confidence=row.get("confidence"),
        )

    def readiness_from_row(self, row: dict[str, Any]) -> ReadinessResult | None:
        if not row.get("readiness_verdict"):
            return None
        adj = row.get("readiness_adjustments")
        if isinstance(adj, str):
            adj = json.loads(adj)
        return ReadinessResult(
            verdict=row["readiness_verdict"],
            weeks_to_race=row.get("weeks_to_race") or 0,
            rationale=row.get("readiness_rationale") or "",
            adjustments=adj or [],
        )

    # ------------------------------------------------------------------
    # Plans
    # ------------------------------------------------------------------

    def save_plan(
        self,
        athlete_id: str,
        plan: TrainingPlan,
        summary: str,
        status: str = "preview",
    ) -> str:
        plan_id = _new_id()
        strength_json = plan.strength_plan.model_dump()
        if self._use_supabase:
            self._sb.table("training_plans").insert(
                {
                    "id": plan_id,
                    "athlete_id": athlete_id,
                    "race_date": plan.athlete_race_date.isoformat(),
                    "total_weeks": plan.total_weeks,
                    "plan_start_date": plan.plan_start_date.isoformat(),
                    "status": status,
                    "strength_plan": strength_json,
                    "summary": summary,
                }
            ).execute()
            for p in plan.phases:
                self._sb.table("phases").insert(
                    {
                        "plan_id": plan_id,
                        "name": p.name.value,
                        "start_week": p.start_week,
                        "end_week": p.end_week,
                        "objective": p.objective,
                    }
                ).execute()
            self._save_workouts_supabase(plan_id, athlete_id, plan)
            self._sb.table("athletes").update({"active_plan_id": plan_id}).eq(
                "id", athlete_id
            ).execute()
            return plan_id

        with self._sqlite() as conn:
            conn.execute(
                """INSERT INTO training_plans
                (id, athlete_id, race_date, total_weeks, plan_start_date, status, strength_plan, summary, created_at)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (
                    plan_id,
                    athlete_id,
                    plan.athlete_race_date.isoformat(),
                    plan.total_weeks,
                    plan.plan_start_date.isoformat(),
                    status,
                    json.dumps(strength_json),
                    summary,
                    _utcnow(),
                ),
            )
            for p in plan.phases:
                conn.execute(
                    """INSERT INTO phases (id, plan_id, name, start_week, end_week, objective)
                    VALUES (?,?,?,?,?,?)""",
                    (_new_id(), plan_id, p.name.value, p.start_week, p.end_week, p.objective),
                )
            self._save_workouts_sqlite(conn, plan_id, athlete_id, plan)
            conn.execute(
                "UPDATE athletes SET active_plan_id = ?, updated_at = ? WHERE id = ?",
                (plan_id, _utcnow(), athlete_id),
            )
        return plan_id

    def _save_workouts_supabase(
        self, plan_id: str, athlete_id: str, plan: TrainingPlan
    ) -> None:
        rows = []
        for week in plan.weeks:
            for w in week.workouts:
                rows.append(
                    {
                        "id": w.id if len(w.id) == 36 else _new_id(),
                        "plan_id": plan_id,
                        "athlete_id": athlete_id,
                        "week_number": week.week_number,
                        "phase": week.phase.value,
                        "sport": w.sport.value,
                        "title": w.title,
                        "description": w.description,
                        "scheduled_date": w.scheduled_date.isoformat()
                        if w.scheduled_date
                        else None,
                        "day_of_week": w.day_of_week,
                        "purpose_tag": w.purpose_tag.value,
                        "is_key_session": w.is_key_session,
                        "steps": [s.model_dump() for s in w.steps],
                        "exercises": [e.model_dump() for e in w.exercises],
                        "estimated_duration_seconds": w.estimated_duration_seconds,
                        "estimated_distance_meters": w.estimated_distance_meters,
                        "estimated_tss": w.estimated_tss,
                        "fueling_notes": w.fueling_notes,
                        "status": w.status.value,
                    }
                )
        if rows:
            self._sb.table("workouts").insert(rows).execute()

    def _save_workouts_sqlite(
        self, conn, plan_id: str, athlete_id: str, plan: TrainingPlan
    ) -> None:
        for week in plan.weeks:
            for w in week.workouts:
                wid = w.id if len(w.id) == 36 else _new_id()
                conn.execute(
                    """INSERT INTO workouts
                    (id, plan_id, athlete_id, week_number, phase, sport, title, description,
                     scheduled_date, day_of_week, purpose_tag, is_key_session, steps, exercises,
                     estimated_duration_seconds, estimated_distance_meters, estimated_tss,
                     fueling_notes, status, created_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        wid,
                        plan_id,
                        athlete_id,
                        week.week_number,
                        week.phase.value,
                        w.sport.value,
                        w.title,
                        w.description,
                        w.scheduled_date.isoformat() if w.scheduled_date else None,
                        w.day_of_week,
                        w.purpose_tag.value,
                        int(w.is_key_session),
                        json.dumps([s.model_dump() for s in w.steps]),
                        json.dumps([e.model_dump() for e in w.exercises]),
                        w.estimated_duration_seconds,
                        w.estimated_distance_meters,
                        w.estimated_tss,
                        w.fueling_notes,
                        w.status.value,
                        _utcnow(),
                    ),
                )

    def activate_plan(self, athlete_id: str, plan_id: str) -> None:
        if self._use_supabase:
            self._sb.table("training_plans").update({"status": "archived"}).eq(
                "athlete_id", athlete_id
            ).neq("id", plan_id).execute()
            self._sb.table("training_plans").update(
                {"status": "active", "activated_at": _utcnow()}
            ).eq("id", plan_id).execute()
            return
        with self._sqlite() as conn:
            conn.execute(
                "UPDATE training_plans SET status='archived' WHERE athlete_id=? AND id!=?",
                (athlete_id, plan_id),
            )
            conn.execute(
                "UPDATE training_plans SET status='active', activated_at=? WHERE id=?",
                (_utcnow(), plan_id),
            )

    def get_current_plan(self, athlete_id: str) -> dict[str, Any] | None:
        if self._use_supabase:
            res = (
                self._sb.table("training_plans")
                .select("*, phases(*)")
                .eq("athlete_id", athlete_id)
                .in_("status", ["active", "preview"])
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            return res.data[0] if res.data else None
        with self._sqlite() as conn:
            row = conn.execute(
                """SELECT * FROM training_plans
                WHERE athlete_id = ? AND status IN ('active','preview')
                ORDER BY created_at DESC LIMIT 1""",
                (athlete_id,),
            ).fetchone()
            if not row:
                return None
            plan = dict(row)
            plan["strength_plan"] = json.loads(plan["strength_plan"])
            phases = conn.execute(
                "SELECT * FROM phases WHERE plan_id = ? ORDER BY start_week",
                (plan["id"],),
            ).fetchall()
            plan["phases"] = [dict(p) for p in phases]
            return plan

    def list_workouts(
        self,
        athlete_id: str,
        sport: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        if self._use_supabase:
            q = self._sb.table("workouts").select("*").eq("athlete_id", athlete_id)
            if sport:
                q = q.eq("sport", sport)
            if status:
                q = q.eq("status", status)
            return q.order("week_number").order("day_of_week").execute().data

        sql = "SELECT * FROM workouts WHERE athlete_id = ?"
        params: list[Any] = [athlete_id]
        if sport:
            sql += " AND sport = ?"
            params.append(sport)
        if status:
            sql += " AND status = ?"
            params.append(status)
        sql += " ORDER BY week_number, day_of_week"
        with self._sqlite() as conn:
            rows = conn.execute(sql, params).fetchall()
            out = []
            for r in rows:
                d = dict(r)
                d["steps"] = json.loads(d["steps"])
                d["exercises"] = json.loads(d["exercises"])
                d["is_key_session"] = bool(d["is_key_session"])
                out.append(d)
            return out

    def get_workout(self, workout_id: str, athlete_id: str) -> dict[str, Any] | None:
        if self._use_supabase:
            res = (
                self._sb.table("workouts")
                .select("*")
                .eq("id", workout_id)
                .eq("athlete_id", athlete_id)
                .limit(1)
                .execute()
            )
            return res.data[0] if res.data else None
        with self._sqlite() as conn:
            row = conn.execute(
                "SELECT * FROM workouts WHERE id = ? AND athlete_id = ?",
                (workout_id, athlete_id),
            ).fetchone()
            if not row:
                return None
            d = dict(row)
            d["steps"] = json.loads(d["steps"])
            d["exercises"] = json.loads(d["exercises"])
            d["is_key_session"] = bool(d["is_key_session"])
            return d

    def complete_workout(
        self,
        workout_id: str,
        athlete_id: str,
        completion: WorkoutCompletion,
    ) -> dict[str, Any]:
        cid = _new_id()
        if self._use_supabase:
            self._sb.table("workout_completions").insert(
                {
                    "id": cid,
                    "workout_id": workout_id,
                    "athlete_id": athlete_id,
                    "completed": completion.completed,
                    "rpe": completion.rpe,
                    "readiness_score": completion.readiness_score,
                    "fatigue_flags": completion.fatigue_flags,
                    "notes": completion.notes,
                }
            ).execute()
            status = "completed" if completion.completed else "skipped"
            self._sb.table("workouts").update({"status": status}).eq(
                "id", workout_id
            ).execute()
        else:
            with self._sqlite() as conn:
                conn.execute(
                    """INSERT INTO workout_completions
                    (id, workout_id, athlete_id, completed, rpe, readiness_score,
                     fatigue_flags, notes, completed_at)
                    VALUES (?,?,?,?,?,?,?,?,?)""",
                    (
                        cid,
                        workout_id,
                        athlete_id,
                        int(completion.completed),
                        completion.rpe,
                        completion.readiness_score,
                        json.dumps(completion.fatigue_flags),
                        completion.notes,
                        _utcnow(),
                    ),
                )
                status = "completed" if completion.completed else "skipped"
                conn.execute(
                    "UPDATE workouts SET status = ? WHERE id = ?",
                    (status, workout_id),
                )
        return {"id": cid, "workout_id": workout_id, "status": status}

    def list_completions(self, athlete_id: str, limit: int = 50) -> list[dict[str, Any]]:
        if self._use_supabase:
            return (
                self._sb.table("workout_completions")
                .select("*, workouts(*)")
                .eq("athlete_id", athlete_id)
                .order("completed_at", desc=True)
                .limit(limit)
                .execute()
                .data
            )
        with self._sqlite() as conn:
            rows = conn.execute(
                """SELECT c.*, w.title, w.sport, w.week_number
                FROM workout_completions c
                JOIN workouts w ON w.id = c.workout_id
                WHERE c.athlete_id = ?
                ORDER BY c.completed_at DESC LIMIT ?""",
                (athlete_id, limit),
            ).fetchall()
            out = []
            for r in rows:
                d = dict(r)
                ff = d.get("fatigue_flags")
                if isinstance(ff, str):
                    d["fatigue_flags"] = json.loads(ff)
                out.append(d)
            return out

    def completions_for_adaptation(self, athlete_id: str) -> list[WorkoutCompletion]:
        rows = self.list_completions(athlete_id, limit=20)
        out = []
        for r in rows:
            sport_val = r.get("sport") or Sport.OTHER
            out.append(
                WorkoutCompletion(
                    workout_id=r["workout_id"],
                    sport=sport_val,
                    completed=bool(r["completed"]),
                    rpe=r.get("rpe"),
                    readiness_score=r.get("readiness_score"),
                    fatigue_flags=r.get("fatigue_flags") or [],
                    notes=r.get("notes"),
                )
            )
        return out

    def save_adaptation(
        self,
        athlete_id: str,
        plan_id: str | None,
        result: AdaptationResult,
        user_accepted: bool | None = None,
    ) -> str:
        eid = _new_id()
        data = {
            "id": eid,
            "athlete_id": athlete_id,
            "plan_id": plan_id,
            "decision": result.decision.value,
            "signals": result.signals,
            "changes": result.changes,
            "rationale": result.rationale,
            "user_accepted": user_accepted,
        }
        if self._use_supabase:
            self._sb.table("adaptation_events").insert(data).execute()
            return eid
        with self._sqlite() as conn:
            conn.execute(
                """INSERT INTO adaptation_events
                (id, athlete_id, plan_id, decision, signals, changes, rationale,
                 user_accepted, triggered_at)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (
                    eid,
                    athlete_id,
                    plan_id,
                    result.decision.value,
                    json.dumps(result.signals),
                    json.dumps(result.changes),
                    result.rationale,
                    user_accepted,
                    _utcnow(),
                ),
            )
        return eid

    def get_pending_adaptation(self, athlete_id: str) -> dict[str, Any] | None:
        if self._use_supabase:
            res = (
                self._sb.table("adaptation_events")
                .select("*")
                .eq("athlete_id", athlete_id)
                .is_("user_accepted", "null")
                .order("triggered_at", desc=True)
                .limit(1)
                .execute()
            )
            return res.data[0] if res.data else None
        with self._sqlite() as conn:
            row = conn.execute(
                """SELECT * FROM adaptation_events
                WHERE athlete_id = ? AND user_accepted IS NULL
                ORDER BY triggered_at DESC LIMIT 1""",
                (athlete_id,),
            ).fetchone()
            if not row:
                return None
            d = dict(row)
            for k in ("signals", "changes"):
                if isinstance(d[k], str):
                    d[k] = json.loads(d[k])
            return d

    def accept_adaptation(self, event_id: str, accepted: bool) -> None:
        if self._use_supabase:
            self._sb.table("adaptation_events").update(
                {"user_accepted": accepted}
            ).eq("id", event_id).execute()
            return
        with self._sqlite() as conn:
            conn.execute(
                "UPDATE adaptation_events SET user_accepted = ? WHERE id = ?",
                (int(accepted), event_id),
            )

    # ------------------------------------------------------------------
    # Chat
    # ------------------------------------------------------------------

    def get_or_create_chat(
        self, athlete_id: str, context: str
    ) -> dict[str, Any]:
        if self._use_supabase:
            res = (
                self._sb.table("chat_conversations")
                .select("*")
                .eq("athlete_id", athlete_id)
                .eq("context", context)
                .limit(1)
                .execute()
            )
            if res.data:
                return res.data[0]
            row = (
                self._sb.table("chat_conversations")
                .insert({"athlete_id": athlete_id, "context": context, "messages": []})
                .execute()
            )
            return row.data[0]

        with self._sqlite() as conn:
            row = conn.execute(
                "SELECT * FROM chat_conversations WHERE athlete_id=? AND context=?",
                (athlete_id, context),
            ).fetchone()
            if row:
                d = dict(row)
                d["messages"] = json.loads(d["messages"])
                return d
            cid = _new_id()
            conn.execute(
                """INSERT INTO chat_conversations
                (id, athlete_id, context, messages, created_at, updated_at)
                VALUES (?,?,?,?,?,?)""",
                (cid, athlete_id, context, "[]", _utcnow(), _utcnow()),
            )
            return {"id": cid, "athlete_id": athlete_id, "context": context, "messages": []}

    def save_chat_messages(
        self, conversation_id: str, messages: list[dict[str, str]]
    ) -> None:
        if self._use_supabase:
            self._sb.table("chat_conversations").update(
                {"messages": messages, "updated_at": _utcnow()}
            ).eq("id", conversation_id).execute()
            return
        with self._sqlite() as conn:
            conn.execute(
                "UPDATE chat_conversations SET messages=?, updated_at=? WHERE id=?",
                (json.dumps(messages), _utcnow(), conversation_id),
            )


_store: Store | None = None


def get_store() -> Store:
    global _store
    if _store is None:
        _store = Store()
    return _store
