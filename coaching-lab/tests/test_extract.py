"""Tests for onboarding profile extraction helpers."""

from __future__ import annotations

from engine.extract import conversation_is_ready, strip_ready_token

SCREENSHOT_MESSAGE = (
    "Got it. We'll incorporate exercises to enhance your hip mobility and strengthen "
    "your hamstrings, which will be beneficial for both your running and cycling. "
    "I have all the information I need to start building your training plan. "
    "I'll put together something that fits your goals and current situation."
)


def test_conversation_is_ready_detects_token():
    assert conversation_is_ready("Sounds good.\n[[READY_TO_BUILD]]")
    assert not conversation_is_ready("Still gathering info.")


def test_conversation_is_ready_detects_natural_language():
    assert conversation_is_ready(SCREENSHOT_MESSAGE)
    assert conversation_is_ready("Great — I'm putting your plan together now.")
    assert conversation_is_ready("I've got everything I need. One moment.")


def test_conversation_is_ready_false_when_still_asking():
    assert not conversation_is_ready("What race are you targeting?")
    assert not conversation_is_ready(
        "I have all the information I need — does that sound right?"
    )


def test_strip_ready_token():
    assert strip_ready_token("Done.\n[[READY_TO_BUILD]]") == "Done."
