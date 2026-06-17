"""Validate LLM adaptation proposals against canonical playbook decisions."""

from __future__ import annotations

from dataclasses import dataclass

from engine.models import AdaptationDecision, ConformanceStatus, LlmAdaptationProposal


@dataclass(frozen=True, slots=True)
class ConformanceResult:
    status: ConformanceStatus
    accepted_rationale: str | None = None
    playbook_rule_cited: str | None = None


def validate_playbook_conformance(
    proposal: LlmAdaptationProposal | None,
    canonical_decision: AdaptationDecision,
) -> ConformanceResult:
    """LLM decision must match canonical; rationale accepted only on match."""
    if proposal is None:
        return ConformanceResult(status=ConformanceStatus.SKIPPED)

    if proposal.decision == canonical_decision:
        return ConformanceResult(
            status=ConformanceStatus.MATCHED,
            accepted_rationale=proposal.rationale,
            playbook_rule_cited=proposal.playbook_rule_cited or None,
        )

    return ConformanceResult(status=ConformanceStatus.REJECTED)
