"""Extract a structured AthleteProfile from the onboarding conversation.

The LLM converses and extracts; deterministic rules act on the result.
"""

from __future__ import annotations

import json
import re

from engine import llm
from engine.models import AthleteProfile
from engine.prompts import EXTRACTION_SYSTEM

READY_TOKEN = "[[READY_TO_BUILD]]"

# Fallback when the coach signals completion in natural language but omits the token.
_READY_PHRASES = (
    re.compile(r"i have all the information i need", re.I),
    re.compile(r"start building your (?:training )?plan", re.I),
    re.compile(r"putting (?:your |together )?(?:training )?plan together", re.I),
    re.compile(r"i(?:'ve| have) got (?:everything|what) i need", re.I),
)


def conversation_is_ready(assistant_message: str) -> bool:
    """True when the onboarding coach signals it has enough info."""
    if READY_TOKEN in assistant_message:
        return True
    text = assistant_message.strip()
    if not text or text.endswith("?"):
        return False
    return any(pattern.search(text) for pattern in _READY_PHRASES)


def strip_ready_token(text: str) -> str:
    return text.replace(READY_TOKEN, "").strip()


def _profile_json_schema() -> dict:
    """JSON schema for OpenAI structured output.

    Hand-written (rather than from Pydantic) to keep the LLM contract explicit
    and stable. Pydantic still validates the result.
    """
    return {
        "type": "object",
        "properties": {
            "goal_type": {"type": "string", "enum": ["finish", "pr", "return"]},
            "race_name": {"type": "string"},
            "race_date": {"type": "string", "description": "ISO date YYYY-MM-DD"},
            "weekly_hours": {"type": "number"},
            "limiter_discipline": {
                "type": "string",
                "enum": ["swim", "bike", "run"],
            },
            "experience_level": {
                "type": "string",
                "enum": ["beginner", "intermediate", "advanced"],
            },
            "available_days": {
                "type": "array",
                "items": {"type": "integer", "minimum": 0, "maximum": 6},
            },
            "injury_flags": {"type": "array", "items": {"type": "string"}},
            "strength_background": {
                "type": "string",
                "enum": ["none", "beginner", "intermediate", "experienced"],
            },
            "strength_equipment": {
                "type": "string",
                "enum": ["gym", "home", "minimal"],
            },
            "current_strength_routine": {"type": ["string", "null"]},
            "strength_restrictions": {"type": "array", "items": {"type": "string"}},
            "confidence": {"type": ["string", "null"]},
        },
        "required": [
            "goal_type",
            "race_name",
            "race_date",
            "weekly_hours",
            "limiter_discipline",
            "experience_level",
            "available_days",
        ],
    }


def _format_conversation(messages: list[dict]) -> str:
    lines = []
    for m in messages:
        role = "Athlete" if m["role"] == "user" else "Coach"
        lines.append(f"{role}: {m['content']}")
    return "\n".join(lines)


def _sanitize_profile_data(data: dict) -> dict:
    """Normalize LLM output before Pydantic validation."""
    out = dict(data)

    for key in ("current_strength_routine", "confidence"):
        if out.get(key) == "":
            out[key] = None

    race_date = out.get("race_date")
    if not race_date or (isinstance(race_date, str) and not race_date.strip()):
        raise ValueError(
            "Race date is missing from the conversation. "
            "Please tell your coach which race you're targeting and when it is."
        )

    return out


def extract_profile(messages: list[dict]) -> AthleteProfile:
    """Call the LLM to extract a validated AthleteProfile from the chat."""
    conversation = _format_conversation(messages)
    raw = llm.complete_json(
        system=EXTRACTION_SYSTEM,
        user_content=f"Conversation:\n\n{conversation}",
        schema=_profile_json_schema(),
        model=llm.extract_model(),
    )
    data = _sanitize_profile_data(json.loads(raw))
    return AthleteProfile.model_validate(data)
