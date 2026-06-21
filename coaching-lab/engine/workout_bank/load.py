from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from engine.workout_bank.models import BankWorkout

_DATA_DIR = Path(__file__).resolve().parent / "data"


def _load_file(name: str) -> list[BankWorkout]:
    path = _DATA_DIR / name
    data = json.loads(path.read_text(encoding="utf-8"))
    return [BankWorkout.model_validate(item) for item in data]


@lru_cache(maxsize=1)
def all_bank_workouts() -> list[BankWorkout]:
    return (
        _load_file("cycling.json")
        + _load_file("running.json")
        + _load_file("swimming.json")
    )


@lru_cache(maxsize=1)
def bank_workouts_by_id() -> dict[str, BankWorkout]:
    return {w.id: w for w in all_bank_workouts()}


def get_bank_workout(bank_workout_id: str | None) -> BankWorkout | None:
    if not bank_workout_id:
        return None
    return bank_workouts_by_id().get(bank_workout_id)
