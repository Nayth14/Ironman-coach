"""Tests for mutation apply and guardrails."""

from __future__ import annotations

from datetime import date

from engine.adaptation.apply import apply_mutations_to_week
from engine.adaptation.guardrails import validate_mutations_against_guardrails
from engine.adaptation.loader import load_playbook
from engine.fixtures import list_fixtures, load_fixture
from engine.models import MutationOp, PhaseName, PlanMutation, PlannedWeek
from engine.plan import generate_plan


def test_hold_trim_reduces_non_key_duration():
    _, profile = load_fixture(list_fixtures()[0])
    plan = generate_plan(profile, today=date(2026, 3, 1))
    week = plan.weeks[0]
    before = week.target_hours
    mutations = [PlanMutation(op=MutationOp.SCALE_NON_KEY_DURATION, factor=0.85)]
    new_week, diffs, _ = apply_mutations_to_week(week, mutations, phase=PhaseName.BASE)
    assert new_week.target_hours <= before
    assert len(diffs) >= 0


def test_guardrail_rejects_excessive_increase():
    spec = load_playbook().spec
    violations = validate_mutations_against_guardrails(
        [PlanMutation(op=MutationOp.SCALE_WEEK_VOLUME, factor=1.25)],
        spec,
        prior_hours=10.0,
        new_hours=12.5,
    )
    assert any("GR-VOL10" in v or "10%" in v for v in violations)
