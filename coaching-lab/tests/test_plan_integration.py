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
    key_bike_run = [
        w
        for w in all_workouts
        if w.sport.value in ("bike", "run") and w.is_key_session
    ]
    assert any(w.bank_workout_id for w in key_bike_run)
    assert all(w.bank_workout_id is None for w in all_workouts if w.title == "Easy run")

    swim_workouts = [w for w in all_workouts if w.sport.value == "swim"]
    assert swim_workouts, "expected at least one swim session in generated plan"
    assert all(w.bank_workout_id for w in swim_workouts)
    assert all(w.description for w in swim_workouts)

    # Strength prescription differs by phase when weeks span phases
    strength_plans = [w.strength_plan for w in tp.weeks if w.strength_plan]
    assert len(strength_plans) == 4


def test_experienced_pr_generates_without_ruleset_violation(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _, profile = fixtures.load_fixture("experienced_pr")
    tp = plan_builder.generate_plan(profile)
    assert len(tp.weeks) == 4
    base_week = next(w for w in tp.weeks if w.phase.value == "base" and not w.is_deload)
    titles = {w.title for w in base_week.workouts}
    assert "Run tempo" not in titles or "Long run" in titles
