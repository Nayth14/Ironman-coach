"""Integration test for full plan generation."""

from __future__ import annotations

from datetime import date

from engine import fixtures, plan as plan_builder


def test_generate_plan_has_dates_and_steps(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _, profile = fixtures.load_fixture("beginner_first_im")
    tp = plan_builder.generate_plan(profile, today=date(2026, 6, 10))

    assert tp.plan_start_date == date(2026, 6, 15)
    assert len(tp.weeks) == 4
    assert tp.weeks[0].strength_plan is not None

    all_workouts = [w for week in tp.weeks for w in week.workouts]
    assert len(all_workouts) > 0
    assert all(w.scheduled_date is not None for w in all_workouts)
    assert all(len(w.steps) >= 3 for w in all_workouts)

    # Strength prescription differs by phase when weeks span phases
    strength_plans = [w.strength_plan for w in tp.weeks if w.strength_plan]
    assert len(strength_plans) == 4
