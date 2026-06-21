"""LLM enrichment: fill workout steps after deterministic scheduling."""

from __future__ import annotations

import json
import os
import uuid
from typing import Any

from engine import llm
from engine.models import (
    AthleteProfile,
    PhaseName,
    PlannedWeek,
    PurposeTag,
    Sport,
    TargetType,
    Workout,
    WorkoutStep,
    WorkoutStepType,
    WorkoutTarget,
)
from engine.prompts import WORKOUT_STEPS_SYSTEM
from engine.workout_bank.expand import expand_bank_workout_steps
from engine.workout_bank.load import get_bank_workout

_DURATION_TOLERANCE = 0.15


def _new_step_id() -> str:
    return uuid.uuid4().hex[:12]


def _workout_steps_schema() -> dict:
    step_schema = {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "type": {
                "type": "string",
                "enum": ["warmup", "work", "recovery", "rest", "cooldown", "repeat"],
            },
            "name": {"type": ["string", "null"]},
            "duration_seconds": {"type": ["integer", "null"]},
            "distance_meters": {"type": ["number", "null"]},
            "target": {
                "type": ["object", "null"],
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["pace", "power", "heart_rate", "rpe", "cadence", "open"],
                    },
                    "min": {"type": ["number", "null"]},
                    "max": {"type": ["number", "null"]},
                    "unit": {"type": ["string", "null"]},
                    "label": {"type": ["string", "null"]},
                },
            },
            "notes": {"type": ["string", "null"]},
            "repeat_count": {"type": ["integer", "null"]},
        },
        "required": ["id", "type"],
    }
    return {
        "type": "object",
        "properties": {
            "workouts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "description": {"type": ["string", "null"]},
                        "steps": {
                            "type": "array",
                            "items": step_schema,
                        },
                    },
                    "required": ["id", "steps"],
                },
            }
        },
        "required": ["workouts"],
    }


def _rpe_for_purpose(purpose: PurposeTag) -> WorkoutTarget:
    if purpose in (PurposeTag.THRESHOLD, PurposeTag.VO2):
        return WorkoutTarget(type=TargetType.RPE, min=7, max=8, label="Threshold RPE 7-8")
    if purpose == PurposeTag.RACE_EXECUTION:
        return WorkoutTarget(type=TargetType.RPE, min=6, max=7, label="Race pace RPE 6-7")
    return WorkoutTarget(type=TargetType.RPE, min=2, max=4, label="Easy RPE 2-4")


def _step_duration_sum(steps: list[WorkoutStep]) -> int:
    total = 0
    for step in steps:
        if step.duration_seconds:
            count = step.repeat_count or 1
            total += step.duration_seconds * count
    return total


def _duration_valid(steps: list[WorkoutStep], target_seconds: int | None) -> bool:
    if not target_seconds or target_seconds <= 0:
        return len(steps) > 0
    actual = _step_duration_sum(steps)
    low = target_seconds * (1 - _DURATION_TOLERANCE)
    high = target_seconds * (1 + _DURATION_TOLERANCE)
    return low <= actual <= high


def _has_endurance_structure(steps: list[WorkoutStep]) -> bool:
    types = {s.type for s in steps}
    return (
        WorkoutStepType.WARMUP in types
        and WorkoutStepType.WORK in types
        and WorkoutStepType.COOLDOWN in types
    )


_VALID_STEP_TYPES = {t.value for t in WorkoutStepType}
_VALID_TARGET_TYPES = {t.value for t in TargetType}

# LLM sometimes uses invalid step types — map to canonical values.
_STEP_TYPE_ALIASES: dict[str, str] = {
    "notes": "work",
    "note": "work",
    "instruction": "work",
    "instructions": "work",
    "main": "work",
    "mainset": "work",
    "interval": "work",
    "intervals": "work",
    "easy": "recovery",
    "active_recovery": "recovery",
    "warm_up": "warmup",
    "warm-up": "warmup",
    "cool_down": "cooldown",
    "cool-down": "cooldown",
}


def _normalize_step_type(raw: str | None) -> str:
    if not raw:
        return WorkoutStepType.WORK.value
    key = raw.strip().lower().replace(" ", "_")
    if key in _VALID_STEP_TYPES:
        return key
    return _STEP_TYPE_ALIASES.get(key, WorkoutStepType.WORK.value)


def _normalize_target(raw: dict | None) -> dict | None:
    if not raw or not isinstance(raw, dict):
        return None
    out = dict(raw)
    t = out.get("type")
    if t and str(t).lower() not in _VALID_TARGET_TYPES:
        out["type"] = TargetType.OPEN.value
    return out


def _sanitize_step_item(item: dict) -> dict:
    """Coerce LLM step JSON into something WorkoutStep accepts."""
    out = dict(item)
    raw_type = str(out.get("type", "")).lower()

    # "notes" as type → work step; preserve text in notes field
    if raw_type in ("notes", "note", "instruction", "instructions"):
        text = out.get("notes") or out.get("name") or out.get("description")
        out["type"] = WorkoutStepType.WORK.value
        if text and not out.get("notes"):
            out["notes"] = str(text)
        if not out.get("name"):
            out["name"] = "Coaching note"
    else:
        out["type"] = _normalize_step_type(out.get("type"))

    if out.get("target"):
        out["target"] = _normalize_target(out["target"])

    nested = out.get("steps")
    if isinstance(nested, list):
        out["steps"] = [_sanitize_step_item(s) for s in nested if isinstance(s, dict)]

    return out


def _parse_steps(raw_steps: list[dict]) -> list[WorkoutStep]:
    out: list[WorkoutStep] = []
    for item in raw_steps:
        if not isinstance(item, dict):
            continue
        cleaned = _sanitize_step_item(item)
        if not cleaned.get("id"):
            cleaned["id"] = _new_step_id()
        try:
            out.append(WorkoutStep.model_validate(cleaned))
        except Exception:
            # Skip malformed steps rather than failing the whole plan
            continue
    return out


def _template_endurance_steps(workout: Workout) -> list[WorkoutStep]:
    total = workout.estimated_duration_seconds or 3600
    warmup = max(300, int(total * 0.10))
    cooldown = max(300, int(total * 0.10))
    work = max(600, total - warmup - cooldown)
    target = _rpe_for_purpose(workout.purpose_tag)
    return [
        WorkoutStep(
            id=_new_step_id(),
            type=WorkoutStepType.WARMUP,
            name="Warm up",
            duration_seconds=warmup,
            target=WorkoutTarget(type=TargetType.RPE, min=2, max=3, label="Easy RPE 2-3"),
        ),
        WorkoutStep(
            id=_new_step_id(),
            type=WorkoutStepType.WORK,
            name=workout.title,
            duration_seconds=work,
            target=target,
            notes=workout.fueling_notes,
        ),
        WorkoutStep(
            id=_new_step_id(),
            type=WorkoutStepType.COOLDOWN,
            name="Cool down",
            duration_seconds=cooldown,
            target=WorkoutTarget(type=TargetType.RPE, min=1, max=2, label="Very easy RPE 1-2"),
        ),
    ]


def _template_strength_steps(workout: Workout) -> list[WorkoutStep]:
    total = workout.estimated_duration_seconds or 1800
    warmup = max(300, int(total * 0.15))
    cooldown = max(180, int(total * 0.10))
    exercises = workout.exercises or []
    if not exercises:
        remaining = max(600, total - warmup - cooldown)
        return _template_endurance_steps(
            workout.model_copy(update={"estimated_duration_seconds": remaining})
        )

    per_exercise = max(
        120,
        (total - warmup - cooldown) // max(1, len(exercises)),
    )
    steps: list[WorkoutStep] = [
        WorkoutStep(
            id=_new_step_id(),
            type=WorkoutStepType.WARMUP,
            name="Dynamic warm-up",
            duration_seconds=warmup,
            target=WorkoutTarget(type=TargetType.RPE, min=2, max=3, label="Easy RPE 2-3"),
        ),
    ]
    for ex in exercises:
        steps.append(
            WorkoutStep(
                id=_new_step_id(),
                type=WorkoutStepType.WORK,
                name=f"{ex.name} — {ex.sets}×{ex.reps}",
                duration_seconds=per_exercise,
                target=WorkoutTarget(type=TargetType.RPE, min=5, max=7, label="Moderate RPE 5-7"),
                notes=ex.notes,
            )
        )
    steps.append(
        WorkoutStep(
            id=_new_step_id(),
            type=WorkoutStepType.COOLDOWN,
            name="Stretch and mobility",
            duration_seconds=cooldown,
        )
    )
    return steps


def template_steps_for_workout(workout: Workout) -> list[WorkoutStep]:
    """Deterministic fallback when LLM is unavailable or validation fails."""
    if workout.sport == Sport.STRENGTH:
        return _template_strength_steps(workout)
    return _template_endurance_steps(workout)


def _build_week_payload(
    week: PlannedWeek,
    profile: AthleteProfile,
    phase: PhaseName,
) -> dict[str, Any]:
    workouts_payload = []
    for w in week.workouts:
        entry: dict[str, Any] = {
            "id": w.id,
            "sport": w.sport.value,
            "title": w.title,
            "purpose_tag": w.purpose_tag.value,
            "is_key_session": w.is_key_session,
            "estimated_duration_seconds": w.estimated_duration_seconds,
            "fueling_notes": w.fueling_notes,
            "bank_workout_id": w.bank_workout_id,
        }
        if w.bank_workout_id:
            bw = get_bank_workout(w.bank_workout_id)
            if bw:
                entry["bank_workout"] = {
                    "id": bw.id,
                    "family": bw.family,
                    "main_set": bw.main_set,
                    "intensity_hint": bw.intensity_hint,
                    "warmup_minutes": bw.warmup_minutes,
                    "cooldown_minutes": bw.cooldown_minutes,
                }
        if w.exercises:
            entry["exercises"] = [
                {"name": e.name, "sets": e.sets, "reps": e.reps} for e in w.exercises
            ]
        workouts_payload.append(entry)

    return {
        "athlete": {
            "experience_level": profile.experience_level.value,
            "goal_type": profile.goal_type.value,
            "limiter_discipline": profile.limiter_discipline.value,
            "injury_flags": profile.injury_flags,
            "weekly_hours": profile.weekly_hours,
        },
        "week": {
            "week_number": week.week_number,
            "phase": phase.value,
            "is_deload": week.is_deload,
            "target_hours": week.target_hours,
        },
        "workouts": workouts_payload,
    }


def _apply_llm_result(week: PlannedWeek, data: dict) -> None:
    by_id = {w.id: w for w in week.workouts}
    for item in data.get("workouts", []):
        wid = item.get("id")
        if wid not in by_id:
            continue
        workout = by_id[wid]
        try:
            steps = _parse_steps(item.get("steps") or [])
        except Exception:
            continue
        if not steps:
            continue
        if workout.sport != Sport.STRENGTH and not _has_endurance_structure(steps):
            continue
        if not _duration_valid(steps, workout.estimated_duration_seconds):
            continue
        workout.steps = steps
        if item.get("description"):
            workout.description = item["description"]


def _llm_available() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def _call_llm_for_week(
    week: PlannedWeek,
    profile: AthleteProfile,
    phase: PhaseName,
) -> dict | None:
    payload = _build_week_payload(week, profile, phase)
    user_content = (
        "Generate structured workout steps for each workout below.\n\n"
        + json.dumps(payload, indent=2)
    )
    try:
        raw = llm.complete_json(
            system=WORKOUT_STEPS_SYSTEM,
            user_content=user_content,
            schema=_workout_steps_schema(),
            model=llm.workout_model(),
        )
        return json.loads(raw)
    except Exception:
        return None


def enrich_week_steps(
    week: PlannedWeek,
    profile: AthleteProfile,
    phase: PhaseName,
) -> PlannedWeek:
    """Fill workout steps via LLM (one batch call per week) with template fallback."""
    if _llm_available():
        data = _call_llm_for_week(week, profile, phase)
        if data:
            _apply_llm_result(week, data)
            # Retry once for workouts still missing valid steps
            missing = [
                w
                for w in week.workouts
                if not w.steps
                or (
                    w.sport != Sport.STRENGTH
                    and not _has_endurance_structure(w.steps)
                )
                or not _duration_valid(w.steps, w.estimated_duration_seconds)
            ]
            if missing:
                retry_week = week.model_copy(
                    update={"workouts": missing},
                    deep=True,
                )
                retry_data = _call_llm_for_week(retry_week, profile, phase)
                if retry_data:
                    _apply_llm_result(week, retry_data)

    for workout in week.workouts:
        needs_fallback = (
            not workout.steps
            or (
                workout.sport != Sport.STRENGTH
                and not _has_endurance_structure(workout.steps)
            )
            or not _duration_valid(workout.steps, workout.estimated_duration_seconds)
        )
        if needs_fallback:
            bank_steps = expand_bank_workout_steps(workout)
            workout.steps = bank_steps or template_steps_for_workout(workout)

    return week
