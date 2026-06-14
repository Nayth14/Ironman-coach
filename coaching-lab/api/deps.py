"""FastAPI dependencies."""

from __future__ import annotations

from fastapi import Header, HTTPException

from api.persistence.store import Store, get_store


def store() -> Store:
    return get_store()


async def require_guest(
    x_guest_id: str | None = Header(default=None, alias="X-Guest-Id"),
) -> tuple[str, dict]:
    if not x_guest_id:
        raise HTTPException(status_code=401, detail="X-Guest-Id header required")
    s = get_store()
    athlete = s.get_athlete_by_guest(x_guest_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="Guest not found")
    return x_guest_id, athlete
