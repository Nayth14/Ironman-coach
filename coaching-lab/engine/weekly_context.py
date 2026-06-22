"""Extract structured weekly context from check-in conversations."""

from __future__ import annotations

import json
import os

from engine import llm
from engine.conversation import (
    conversation_is_ready as _convo_ready,
    format_conversation,
    strip_token,
)
from engine.models import WeeklyContext
from engine.prompts import WEEKLY_CONTEXT_EXTRACTION_SYSTEM

READY_TOKEN = "[[READY_TO_EVALUATE]]"


def llm_available() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY", "").strip())


def conversation_is_ready(assistant_message: str) -> bool:
    return _convo_ready(assistant_message, READY_TOKEN)


def strip_ready_token(text: str) -> str:
    return strip_token(text, READY_TOKEN)


def _weekly_context_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "week_number": {"type": ["integer", "null"]},
            "summary": {"type": "string"},
            "fatigue_flags": {"type": "array", "items": {"type": "string"}},
            "illness_days_off": {"type": "integer"},
            "life_stress": {"type": "boolean"},
            "missed_key_reason": {"type": ["string", "null"]},
            "athlete_quotes": {"type": "array", "items": {"type": "string"}},
            "confidence": {
                "type": "string",
                "enum": ["high", "medium", "low"],
            },
        },
        "required": ["summary", "fatigue_flags", "illness_days_off", "life_stress"],
    }


def extract_weekly_context(
    messages: list[dict],
    week_number: int | None = None,
) -> WeeklyContext:
    """Call the LLM to extract playbook-bounded weekly context from chat."""
    conversation = format_conversation(messages)
    week_hint = f"\nReviewed plan week: {week_number}" if week_number else ""
    raw = llm.complete_json(
        system=WEEKLY_CONTEXT_EXTRACTION_SYSTEM,
        user_content=f"Conversation:{week_hint}\n\n{conversation}",
        schema=_weekly_context_schema(),
        model=llm.extract_model(),
    )
    data = json.loads(raw)
    if week_number is not None and not data.get("week_number"):
        data["week_number"] = week_number
    return WeeklyContext.model_validate(data)
