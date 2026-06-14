"""Ironman Coach API — FastAPI service wrapping the coaching engine."""

from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from engine import adaptation, extract, fixtures, plan as plan_builder, readiness
from engine import llm
from engine.models import (
    AthleteProfile,
    ReadinessResult,
    TrainingPlan,
    WorkoutCompletion,
)
from engine.prompts import COACHING_SYSTEM, ONBOARDING_SYSTEM, SUMMARY_SYSTEM

from api.deps import require_guest, store
from api.persistence.store import Store, get_store

load_dotenv()

app = FastAPI(
    title="Ironman Coach API",
    description="Nayth's Ironman Coach — coaching engine API",
    version="1.0.0",
)

_cors_origins = os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class GuestCreate(BaseModel):
    guest_id: str | None = None


class ChatMessage(BaseModel):
    role: str
    content: str


class OnboardingChatRequest(BaseModel):
    messages: list[ChatMessage]


class PlanGenerateRequest(BaseModel):
    messages: list[ChatMessage]


class CompleteWorkoutRequest(BaseModel):
    completed: bool = True
    rpe: int | None = Field(default=None, ge=1, le=10)
    readiness_score: int | None = Field(default=None, ge=1, le=10)
    fatigue_flags: list[str] = Field(default_factory=list)
    notes: str | None = None


class AdaptationAcceptRequest(BaseModel):
    accepted: bool


class CoachingChatRequest(BaseModel):
    messages: list[ChatMessage]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sse_event(event: str, data: Any) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _generate_summary(profile: AthleteProfile, verdict: ReadinessResult, tp: TrainingPlan) -> str:
    phase_lines = ", ".join(
        f"{p.name.value} (wk {p.start_week}-{p.end_week})" for p in tp.phases
    )
    context = (
        f"Profile: {profile.model_dump_json()}\n"
        f"Readiness: {verdict.model_dump_json()}\n"
        f"Strength plan: {tp.strength_plan.model_dump_json()}\n"
        f"Phases: {phase_lines}\n"
        f"Weeks materialized: {len(tp.weeks)}"
    )
    try:
        return llm.complete_chat(
            system=SUMMARY_SYSTEM,
            messages=[{"role": "user", "content": context}],
            model=llm.summary_model(),
        )
    except Exception:
        return (
            f"Your {profile.race_name} plan is ready — {verdict.weeks_to_race} weeks "
            f"to race with a {verdict.verdict.value} readiness verdict. "
            f"We've built {len(tp.weeks)} weeks to start."
        )


def _build_coaching_context(s: Store, athlete: dict) -> str:
    profile = s.profile_from_row(athlete)
    plan_row = s.get_current_plan(athlete["id"])
    workouts = s.list_workouts(athlete["id"])
    completions = s.list_completions(athlete["id"], limit=10)
    parts = []
    if profile:
        parts.append(f"Athlete profile: {profile.model_dump_json()}")
    if plan_row:
        parts.append(
            f"Active plan: {plan_row.get('total_weeks')} weeks, status={plan_row.get('status')}"
        )
        if plan_row.get("phases"):
            parts.append(f"Phases: {json.dumps(plan_row['phases'])}")
    if workouts:
        recent = workouts[:7]
        parts.append(f"This week's workouts: {json.dumps(recent)}")
    if completions:
        parts.append(f"Recent completions: {json.dumps(completions[:5])}")
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/api/health")
def health():
    return {"status": "ok", "storage": "supabase" if get_store()._use_supabase else "sqlite"}


@app.post("/api/guests")
def create_guest(body: GuestCreate | None = None, s: Store = Depends(store)):
    gid = body.guest_id if body else None
    athlete = s.create_guest(gid)
    return {"guestId": athlete["guest_id"], "athleteId": athlete["id"]}


@app.post("/api/chat/onboarding")
def onboarding_chat(body: OnboardingChatRequest, s: Store = Depends(store)):
    messages = [m.model_dump() for m in body.messages]

    def stream():
        full = ""
        try:
            for delta in llm.stream_chat(ONBOARDING_SYSTEM, messages):
                full += delta
                visible = extract.strip_ready_token(full)
                yield _sse_event("token", {"content": delta, "full": visible})
            clean = extract.strip_ready_token(full)
            yield _sse_event("done", {"content": clean, "ready": extract.conversation_is_ready(full)})
        except Exception as exc:
            yield _sse_event("error", {"message": str(exc)})

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.post("/api/plans/generate")
def generate_plan(
    body: PlanGenerateRequest,
    x_guest_id: str | None = Header(default=None, alias="X-Guest-Id"),
    s: Store = Depends(store),
):
    if not x_guest_id:
        raise HTTPException(401, "X-Guest-Id required")

    athlete = s.get_athlete_by_guest(x_guest_id)
    if not athlete:
        athlete = s.create_guest(x_guest_id)

    messages = [m.model_dump() for m in body.messages]
    try:
        profile = extract.extract_profile(messages)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, f"Profile extraction failed: {exc}") from exc

    verdict = readiness.assess(profile)
    tp = plan_builder.generate_plan(profile)
    summary = _generate_summary(profile, verdict, tp)

    s.upsert_athlete_profile(athlete["id"], profile, verdict)
    plan_id = s.save_plan(athlete["id"], tp, summary, status="preview")

    conv = s.get_or_create_chat(athlete["id"], "onboarding")
    s.save_chat_messages(conv["id"], messages)

    return {
        "planId": plan_id,
        "planStartDate": tp.plan_start_date.isoformat(),
        "profile": json.loads(profile.model_dump_json()),
        "readiness": json.loads(verdict.model_dump_json()),
        "plan": json.loads(tp.model_dump_json()),
        "summary": summary,
    }


@app.post("/api/plans/{plan_id}/activate")
def activate_plan(
    plan_id: str,
    guest: tuple[str, dict] = Depends(require_guest),
    s: Store = Depends(store),
):
    _, athlete = guest
    s.activate_plan(athlete["id"], plan_id)
    return {"status": "active", "planId": plan_id}


@app.get("/api/plans/current")
def current_plan(guest: tuple[str, dict] = Depends(require_guest), s: Store = Depends(store)):
    _, athlete = guest
    plan_row = s.get_current_plan(athlete["id"])
    if not plan_row:
        raise HTTPException(404, "No plan found")
    workouts = s.list_workouts(athlete["id"])
    profile = s.profile_from_row(athlete)
    readiness_data = s.readiness_from_row(athlete)
    return {
        "plan": plan_row,
        "planStartDate": plan_row.get("plan_start_date"),
        "workouts": workouts,
        "profile": json.loads(profile.model_dump_json()) if profile else None,
        "readiness": json.loads(readiness_data.model_dump_json()) if readiness_data else None,
    }


@app.get("/api/workouts")
def list_workouts(
    sport: str | None = Query(default=None),
    status: str | None = Query(default=None),
    guest: tuple[str, dict] = Depends(require_guest),
    s: Store = Depends(store),
):
    _, athlete = guest
    return {"workouts": s.list_workouts(athlete["id"], sport=sport, status=status)}


@app.get("/api/workouts/{workout_id}")
def get_workout(
    workout_id: str,
    guest: tuple[str, dict] = Depends(require_guest),
    s: Store = Depends(store),
):
    _, athlete = guest
    w = s.get_workout(workout_id, athlete["id"])
    if not w:
        raise HTTPException(404, "Workout not found")
    return w


@app.patch("/api/workouts/{workout_id}/complete")
def complete_workout(
    workout_id: str,
    body: CompleteWorkoutRequest,
    guest: tuple[str, dict] = Depends(require_guest),
    s: Store = Depends(store),
):
    _, athlete = guest
    w = s.get_workout(workout_id, athlete["id"])
    if not w:
        raise HTTPException(404, "Workout not found")
    completion = WorkoutCompletion(
        workout_id=workout_id,
        sport=w["sport"],
        completed=body.completed,
        rpe=body.rpe,
        readiness_score=body.readiness_score,
        fatigue_flags=body.fatigue_flags,
        notes=body.notes,
    )
    result = s.complete_workout(workout_id, athlete["id"], completion)
    return result


@app.post("/api/adaptations/evaluate")
def evaluate_adaptation(
    guest: tuple[str, dict] = Depends(require_guest),
    s: Store = Depends(store),
):
    _, athlete = guest
    profile = s.profile_from_row(athlete)
    if not profile:
        raise HTTPException(400, "Profile not complete")
    completions = s.completions_for_adaptation(athlete["id"])
    if len(completions) < 1:
        raise HTTPException(400, "Need at least one completion to evaluate")
    result = adaptation.evaluate(profile, completions)
    plan_row = s.get_current_plan(athlete["id"])
    plan_id = plan_row["id"] if plan_row else None
    event_id = s.save_adaptation(athlete["id"], plan_id, result)
    return {
        "eventId": event_id,
        "decision": result.decision.value,
        "signals": result.signals,
        "changes": result.changes,
        "rationale": result.rationale,
    }


@app.get("/api/adaptations/pending")
def pending_adaptation(
    guest: tuple[str, dict] = Depends(require_guest),
    s: Store = Depends(store),
):
    _, athlete = guest
    event = s.get_pending_adaptation(athlete["id"])
    return {"adaptation": event}


@app.post("/api/adaptations/{event_id}/accept")
def accept_adaptation(
    event_id: str,
    body: AdaptationAcceptRequest,
    guest: tuple[str, dict] = Depends(require_guest),
    s: Store = Depends(store),
):
    s.accept_adaptation(event_id, body.accepted)
    return {"eventId": event_id, "accepted": body.accepted}


@app.post("/api/chat/coaching")
def coaching_chat(
    body: CoachingChatRequest,
    guest: tuple[str, dict] = Depends(require_guest),
    s: Store = Depends(store),
):
    _, athlete = guest
    context = _build_coaching_context(s, athlete)
    system = f"{COACHING_SYSTEM}\n\n--- Athlete context ---\n{context}"
    messages = [m.model_dump() for m in body.messages]

    def stream():
        full = ""
        try:
            for delta in llm.stream_chat(system, messages):
                full += delta
                yield _sse_event("token", {"content": delta, "full": full})
            yield _sse_event("done", {"content": full})
            conv = s.get_or_create_chat(athlete["id"], "coaching")
            updated = messages + [{"role": "assistant", "content": full}]
            s.save_chat_messages(conv["id"], updated)
        except Exception as exc:
            yield _sse_event("error", {"message": str(exc)})

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.get("/api/fixtures")
def list_fixtures():
    return {"fixtures": fixtures.list_fixtures()}


@app.post("/api/fixtures/{name}/build")
def build_from_fixture(
    name: str,
    x_guest_id: str | None = Header(default=None, alias="X-Guest-Id"),
    s: Store = Depends(store),
):
    if not x_guest_id:
        raise HTTPException(401, "X-Guest-Id required")
    athlete = s.get_athlete_by_guest(x_guest_id)
    if not athlete:
        athlete = s.create_guest(x_guest_id)

    fixture_name, profile = fixtures.load_fixture(name)
    verdict = readiness.assess(profile)
    tp = plan_builder.generate_plan(profile)
    summary = _generate_summary(profile, verdict, tp)

    s.upsert_athlete_profile(athlete["id"], profile, verdict)
    plan_id = s.save_plan(athlete["id"], tp, summary, status="preview")

    return {
        "fixture": fixture_name,
        "planId": plan_id,
        "planStartDate": tp.plan_start_date.isoformat(),
        "profile": json.loads(profile.model_dump_json()),
        "readiness": json.loads(verdict.model_dump_json()),
        "plan": json.loads(tp.model_dump_json()),
        "summary": summary,
    }


@app.get("/api/athletes/me")
def get_me(guest: tuple[str, dict] = Depends(require_guest), s: Store = Depends(store)):
    _, athlete = guest
    profile = s.profile_from_row(athlete)
    readiness_data = s.readiness_from_row(athlete)
    return {
        "athlete": athlete,
        "profile": json.loads(profile.model_dump_json()) if profile else None,
        "readiness": json.loads(readiness_data.model_dump_json()) if readiness_data else None,
    }
