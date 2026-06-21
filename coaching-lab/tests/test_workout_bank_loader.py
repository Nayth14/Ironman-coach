from __future__ import annotations

from engine.workout_bank.load import all_bank_workouts


def test_workout_bank_counts():
    rows = all_bank_workouts()
    assert len(rows) == 208
    cycling = [w for w in rows if w.sport.value == "bike"]
    running = [w for w in rows if w.sport.value == "run"]
    swimming = [w for w in rows if w.sport.value == "swim"]
    assert len(cycling) == 100
    assert len(running) == 63
    assert len(swimming) == 45


def test_workout_bank_has_swim_technique_ids():
    ids = {w.id for w in all_bank_workouts()}
    assert "TECH60-1" in ids
    assert "AER60-2" in ids
    assert "THR75-3" in ids


def test_workout_bank_has_long_run_and_long_ride_ids():
    ids = {w.id for w in all_bank_workouts()}
    assert "LR120-2" in ids
    assert "LR360-5" in ids
