"""Shared serialization helpers for API responses."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel


def serialize_model(model: BaseModel) -> dict[str, Any]:
    """Convert a Pydantic model to a JSON-safe dict.

    Equivalent to ``json.loads(model.model_dump_json())`` but expressed once
    so callers don't repeat the round-trip pattern everywhere.
    """
    return json.loads(model.model_dump_json())
