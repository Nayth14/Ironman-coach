"""Tests for weekly context helpers."""

from __future__ import annotations

from engine.weekly_context import conversation_is_ready, strip_ready_token


def test_conversation_is_ready_detects_token():
    assert conversation_is_ready("Sounds good.\n[[READY_TO_EVALUATE]]")
    assert not conversation_is_ready("Still gathering info.")


def test_strip_ready_token():
    assert strip_ready_token("Done.\n[[READY_TO_EVALUATE]]") == "Done."
