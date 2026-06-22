"""Shared conversation utilities for onboarding and weekly check-in flows.

Both ``extract`` (onboarding) and ``weekly_context`` (check-in) need to
format chat transcripts and detect ready-to-proceed tokens.  This module
consolidates that logic so it lives in one place.
"""

from __future__ import annotations

import re
from typing import Sequence


def format_conversation(messages: list[dict]) -> str:
    """Render a list of chat messages as a labelled transcript."""
    lines: list[str] = []
    for m in messages:
        role = "Athlete" if m["role"] == "user" else "Coach"
        lines.append(f"{role}: {m['content']}")
    return "\n".join(lines)


def strip_token(text: str, token: str) -> str:
    """Remove a sentinel token from assistant output."""
    return text.replace(token, "").strip()


def conversation_is_ready(
    assistant_message: str,
    token: str,
    fallback_patterns: Sequence[re.Pattern[str]] = (),
) -> bool:
    """Return True when the assistant signals it has enough info.

    Checks for an explicit *token* first, then falls back to natural-language
    patterns if supplied.
    """
    if token in assistant_message:
        return True
    if not fallback_patterns:
        return False
    text = assistant_message.strip()
    if not text or text.endswith("?"):
        return False
    return any(p.search(text) for p in fallback_patterns)
