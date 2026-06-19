"""Ironman Coach API — FastAPI service wrapping the coaching engine."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from engine import adaptation, extract, fixtures, plan as plan_builder, readiness
from engine import llm
from engine import weekly_context as weekly_ctx
from engine.adaptation.telemetry import TelemetryEvent, emit
from engine.models import (
    AdaptationDecision,
    AdaptationResult,
    AthleteProfile,
    PlanMutation,
    PlanState,
    ReadinessResult,
    TrainingPlan,
    WeeklyContext,
    WorkoutCompletion,
)
from engine.prompts import COACHING_SYSTEM, ONBOARDING_SYSTEM, SUMMARY_SYSTEM, WEEKLY_CHECKIN_SYSTEM

from api.deps import require_auth, require_auth_athlete, require_guest, store
from api.persistence.store import Store, get_store

load_dotenv()

logger = logging.getLogger("ironman_coach.auth")

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


class WeeklyCheckinChatRequest(BaseModel):
    messages: list[ChatMessage]


class WeeklyContextExtractRequest(BaseModel):
    messages: list[ChatMessage]
    week_number: int | None = None


class EvaluateAdaptationRequest(BaseModel):
    weekly_checkin_id: str | None = Field(default=None, alias="weeklyCheckinId")

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sse_event(event: str, data: Any) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _summary_fallback(profile: AthleteProfile, verdict: ReadinessResult, tp: TrainingPlan) -> str:
    return (
        f"Your {profile.race_name} plan is ready — {verdict.weeks_to_race} weeks "
        f"to race with a {verdict.verdict.value} readiness verdict. "
        f"We've built {len(tp.weeks)} weeks to start."
    )


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
        return _summary_fallback(profile, verdict, tp)


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


@app.post("/api/auth/link-guest")
def link_guest(
    auth_user_id: str = Depends(require_auth),
    x_guest_id: str | None = Header(default=None, alias="X-Guest-Id"),
    s: Store = Depends(store),
):
    if not x_guest_id:
        raise HTTPException(status_code=401, detail="X-Guest-Id header required")
    try:
        athlete_id = s.link_guest_to_auth(x_guest_id, auth_user_id)
    except Store.GuestNotFoundError:
        raise HTTPException(status_code=404, detail="Guest not found") from None
    except Store.AuthLinkConflictError:
        logger.warning(
            "auth_link_guest_conflict guest_id=%s auth_user_id=%s",
            x_guest_id,
            auth_user_id,
        )
        raise HTTPException(
            status_code=409,
            detail="Auth account already linked to a different profile",
        ) from None

    logger.info(
        "auth_link_guest_success guest_id=%s auth_user_id=%s athlete_id=%s",
        x_guest_id,
        auth_user_id,
        athlete_id,
    )
    return {"athleteId": athlete_id, "linked": True}


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
    # Skip the LLM summary here — extraction already calls OpenAI and the combined
    # request can exceed Netlify/proxy timeouts (~26s).
    summary = _summary_fallback(profile, verdict, tp)

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
    auth: tuple[str, dict] = Depends(require_auth_athlete),
    s: Store = Depends(store),
):
    _, athlete = auth
    s.activate_plan(athlete["id"], plan_id)
    return {"status": "active", "planId": plan_id}


@app.get("/api/plans/current")
def current_plan(auth: tuple[str, dict] = Depends(require_auth_athlete), s: Store = Depends(store)):
    _, athlete = auth
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
    auth: tuple[str, dict] = Depends(require_auth_athlete),
    s: Store = Depends(store),
):
    _, athlete = auth
    return {"workouts": s.list_workouts(athlete["id"], sport=sport, status=status)}


@app.get("/api/workouts/{workout_id}")
def get_workout(
    workout_id: str,
    auth: tuple[str, dict] = Depends(require_auth_athlete),
    s: Store = Depends(store),
):
    _, athlete = auth
    w = s.get_workout(workout_id, athlete["id"])
    if not w:
        raise HTTPException(404, "Workout not found")
    return w


@app.patch("/api/workouts/{workout_id}/complete")
def complete_workout(
    workout_id: str,
    body: CompleteWorkoutRequest,
    auth: tuple[str, dict] = Depends(require_auth_athlete),
    s: Store = Depends(store),
):
    _, athlete = auth
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


@app.post("/api/chat/weekly-checkin")
def weekly_checkin_chat(
    body: WeeklyCheckinChatRequest,
    auth: tuple[str, dict] = Depends(require_auth_athlete),
    s: Store = Depends(store),
):
    _, athlete = auth
    messages = [m.model_dump() for m in body.messages]

    def stream():
        full = ""
        try:
            for delta in llm.stream_chat(WEEKLY_CHECKIN_SYSTEM, messages):
                full += delta
                visible = weekly_ctx.strip_ready_token(full)
                yield _sse_event("token", {"content": delta, "full": visible})
            clean = weekly_ctx.strip_ready_token(full)
            yield _sse_event(
                "done",
                {"content": clean, "ready": weekly_ctx.conversation_is_ready(full)},
            )
        except Exception as exc:
            yield _sse_event("error", {"message": str(exc)})

    conv = s.get_or_create_chat(athlete["id"], "weekly_checkin")
    s.save_chat_messages(conv["id"], messages)

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.post("/api/adaptations/weekly-context/extract")
def extract_weekly_context_endpoint(
    body: WeeklyContextExtractRequest,
    auth: tuple[str, dict] = Depends(require_auth_athlete),
    s: Store = Depends(store),
):
    _, athlete = auth
    if not weekly_ctx.llm_available():
        raise HTTPException(503, "Weekly check-in requires OpenAI configuration")

    messages = [m.model_dump() for m in body.messages]
    plan_row = s.get_current_plan(athlete["id"])
    plan_id = plan_row["id"] if plan_row else None

    try:
        context = weekly_ctx.extract_weekly_context(messages, body.week_number)
    except Exception as exc:
        raise HTTPException(500, f"Weekly context extraction failed: {exc}") from exc

    conv = s.get_or_create_chat(athlete["id"], "weekly_checkin")
    s.save_chat_messages(conv["id"], messages)
    checkin_id = s.save_weekly_checkin(
        athlete["id"],
        plan_id,
        context.week_number or body.week_number,
        conv["id"],
        context,
    )

    return {
        "checkinId": checkin_id,
        "context": json.loads(context.model_dump_json()),
    }


@app.post("/api/adaptations/evaluate")
def evaluate_adaptation(
    body: EvaluateAdaptationRequest = EvaluateAdaptationRequest(),
    auth: tuple[str, dict] = Depends(require_auth_athlete),
    s: Store = Depends(store),
):
    _, athlete = auth
    profile = s.profile_from_row(athlete)
    if not profile:
        raise HTTPException(400, "Profile not complete")
    completions = s.completions_for_adaptation(athlete["id"])
    if len(completions) < 1:
        raise HTTPException(400, "Need at least one completion to evaluate")

    plan_row = s.get_current_plan(athlete["id"])
    plan_id = plan_row["id"] if plan_row else None
    plan_state = s.get_plan_state(plan_id) if plan_id else PlanState()
    training_plan = None
    if plan_row:
        training_plan = s.build_training_plan(athlete["id"], plan_row)

    weekly_context: WeeklyContext | None = None
    weekly_checkin_id: str | None = None
    if body.weekly_checkin_id:
        checkin = s.get_weekly_checkin(body.weekly_checkin_id, athlete["id"])
        if not checkin:
            raise HTTPException(404, "Weekly check-in not found")
        weekly_checkin_id = checkin["id"]
        raw_ctx = checkin.get("extracted_context") or {}
        weekly_context = WeeklyContext.model_validate(raw_ctx)

    result = adaptation.evaluate(
        profile,
        completions,
        plan_state=plan_state,
        plan=training_plan,
        weekly_context=weekly_context,
    )
    event_id = s.save_adaptation(
        athlete["id"], plan_id, result, weekly_checkin_id=weekly_checkin_id
    )
    emit(
        TelemetryEvent.TRIGGERED,
        athlete_id=athlete["id"],
        event_id=event_id,
        decision=result.decision.value,
        playbook_version=result.playbook_version,
    )
    payload = {
        "eventId": event_id,
        "decision": result.decision.value,
        "signals": result.signals,
        "changes": result.changes,
        "rationale": result.rationale,
        "mutations": [m.model_dump() for m in result.mutations],
        "planStateDelta": result.plan_state_delta,
        "playbookVersion": result.playbook_version,
        "insufficientData": result.insufficient_data,
        "reviewedWeekNumber": result.reviewed_week_number,
        "targetWeekNumber": result.target_week_number,
        "weeklyContextSummary": result.weekly_context_summary,
        "conformanceStatus": (
            result.conformance_status.value if result.conformance_status else None
        ),
        "playbookRuleCited": result.playbook_rule_cited,
    }
    if result.diff:
        payload["diff"] = result.diff.model_dump()
    return payload


@app.get("/api/adaptations/pending")
def pending_adaptation(
    auth: tuple[str, dict] = Depends(require_auth_athlete),
    s: Store = Depends(store),
):
    _, athlete = auth
    event = s.get_pending_adaptation(athlete["id"])
    if event:
        event = _serialize_adaptation_event(event)
    return {"adaptation": event}


def _serialize_adaptation_event(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "eventId": event.get("id"),
        "id": event.get("id"),
        "decision": event.get("decision"),
        "signals": event.get("signals") or [],
        "changes": event.get("changes") or [],
        "rationale": event.get("rationale"),
        "mutations": event.get("proposed_mutations") or [],
        "planStateDelta": event.get("plan_state_delta") or {},
        "playbookVersion": event.get("playbook_version"),
        "diff": event.get("diff"),
        "reviewedWeekNumber": event.get("reviewed_week_number"),
        "targetWeekNumber": event.get("target_week_number"),
        "weeklyContextSummary": event.get("weekly_context_summary"),
        "conformanceStatus": event.get("conformance_status"),
        "playbookRuleCited": event.get("playbook_rule_cited"),
        "user_accepted": event.get("user_accepted"),
        "applicationStatus": event.get("application_status"),
    }


@app.post("/api/adaptations/{event_id}/accept")
def accept_adaptation(
    event_id: str,
    body: AdaptationAcceptRequest,
    auth: tuple[str, dict] = Depends(require_auth_athlete),
    s: Store = Depends(store),
):
    _, athlete = auth
    event = s.get_adaptation_event(event_id)
    if not event:
        raise HTTPException(404, "Adaptation event not found")

    s.accept_adaptation(event_id, body.accepted)

    if not body.accepted:
        emit(
            TelemetryEvent.DISMISSED,
            athlete_id=athlete["id"],
            event_id=event_id,
            decision=event.get("decision"),
            playbook_version=event.get("playbook_version"),
        )
        return {"eventId": event_id, "accepted": False, "applied": False}

    plan_id = event.get("plan_id")
    if not plan_id:
        emit(TelemetryEvent.APPLY_FAILURE, athlete_id=athlete["id"], event_id=event_id)
        return {"eventId": event_id, "accepted": True, "applied": False, "error": "No plan"}

    plan_row = s.get_current_plan(athlete["id"])
    if not plan_row:
        raise HTTPException(404, "Plan not found")

    profile = s.profile_from_row(athlete)
    training_plan = s.build_training_plan(athlete["id"], plan_row)
    plan_state = s.get_plan_state(plan_id)

    mutations = [
        PlanMutation.model_validate(m) for m in (event.get("proposed_mutations") or [])
    ]
    result = AdaptationResult(
        decision=AdaptationDecision(event["decision"]),
        signals=event.get("signals") or [],
        changes=event.get("changes") or [],
        rationale=event.get("rationale") or "",
        mutations=mutations,
        plan_state_delta=event.get("plan_state_delta") or {},
        playbook_version=event.get("playbook_version"),
        diff=None,
        reviewed_week_number=event.get("reviewed_week_number"),
        target_week_number=event.get("target_week_number"),
    )

    try:
        s.apply_adaptation_event(
            event_id, athlete["id"], training_plan, plan_id, result
        )
        emit(
            TelemetryEvent.APPLY_SUCCESS,
            athlete_id=athlete["id"],
            event_id=event_id,
            decision=result.decision.value,
            playbook_version=result.playbook_version,
        )
        return {"eventId": event_id, "accepted": True, "applied": True}
    except Exception as exc:
        logger.exception("adaptation apply failed")
        emit(
            TelemetryEvent.APPLY_FAILURE,
            athlete_id=athlete["id"],
            event_id=event_id,
            extra={"error": str(exc)},
        )
        if not s._use_supabase:
            with s._sqlite() as conn:
                conn.execute(
                    """UPDATE adaptation_events SET application_status='failed',
                    application_error=? WHERE id=?""",
                    (str(exc), event_id),
                )
        return {
            "eventId": event_id,
            "accepted": True,
            "applied": False,
            "error": str(exc),
        }


@app.post("/api/chat/coaching")
def coaching_chat(
    body: CoachingChatRequest,
    auth: tuple[str, dict] = Depends(require_auth_athlete),
    s: Store = Depends(store),
):
    _, athlete = auth
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
def get_me(auth: tuple[str, dict] = Depends(require_auth_athlete), s: Store = Depends(store)):
    _, athlete = auth
    profile = s.profile_from_row(athlete)
    readiness_data = s.readiness_from_row(athlete)
    return {
        "athlete": athlete,
        "profile": json.loads(profile.model_dump_json()) if profile else None,
        "readiness": json.loads(readiness_data.model_dump_json()) if readiness_data else None,
    }
