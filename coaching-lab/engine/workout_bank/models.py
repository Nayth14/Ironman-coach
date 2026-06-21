from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from engine.models import PurposeTag, Sport


class BankWorkout(BaseModel):
    id: str
    sport: Sport
    category: Literal["interval", "long"]
    family: str
    title: str
    main_set: str
    duration_minutes: int
    purpose_tag: PurposeTag
    is_key_session: bool = True
    estimated_tss: float | None = None
    intensity_hint: str | None = None
    phases: list[str] = []
    warmup_minutes: int | None = None
    cooldown_minutes: int | None = None
