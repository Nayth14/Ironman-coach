"""Tests for playbook conformance validation."""

from __future__ import annotations

from engine.adaptation.conformance import validate_playbook_conformance
from engine.models import (
    AdaptationDecision,
    ConformanceStatus,
    LlmAdaptationProposal,
    WeeklyContext,
)


def _proposal(decision: AdaptationDecision) -> LlmAdaptationProposal:
    return LlmAdaptationProposal(
        decision=decision,
        rationale="Personalized note.",
        signal_augmentations=WeeklyContext(summary="test"),
        playbook_rule_cited="§5.4",
        confidence="high",
    )


def test_matching_decision_accepts_rationale():
    result = validate_playbook_conformance(
        _proposal(AdaptationDecision.HOLD),
        AdaptationDecision.HOLD,
    )
    assert result.status == ConformanceStatus.MATCHED
    assert result.accepted_rationale == "Personalized note."
    assert result.playbook_rule_cited == "§5.4"


def test_mismatched_decision_rejected():
    result = validate_playbook_conformance(
        _proposal(AdaptationDecision.PROGRESS),
        AdaptationDecision.HOLD,
    )
    assert result.status == ConformanceStatus.REJECTED
    assert result.accepted_rationale is None


def test_no_proposal_skipped():
    result = validate_playbook_conformance(None, AdaptationDecision.HOLD)
    assert result.status == ConformanceStatus.SKIPPED
