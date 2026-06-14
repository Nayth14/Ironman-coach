"""FastAPI dependencies."""

from __future__ import annotations

import os

import jwt
from fastapi import Depends, Header, HTTPException

from api.persistence.store import Store, get_store


def store() -> Store:
    return get_store()


def _extract_bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1].strip()
    return token or None


def verify_access_token(token: str) -> str:
    """Verify JWT and return auth user id (sub claim)."""
    secret = os.environ.get("SUPABASE_JWT_SECRET")
    try:
        if secret:
            payload = jwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
        else:
            payload = jwt.decode(
                token,
                options={"verify_signature": False},
                algorithms=["HS256"],
                audience="authenticated",
            )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid token: missing sub")
    return str(sub)


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


async def require_auth(
    authorization: str | None = Header(default=None),
) -> str:
    token = _extract_bearer(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Authorization Bearer token required")
    return verify_access_token(token)


async def require_auth_athlete(
    auth_user_id: str = Depends(require_auth),
) -> tuple[str, dict]:
    s = get_store()
    athlete = s.get_athlete_by_auth_user(auth_user_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")
    return auth_user_id, athlete
