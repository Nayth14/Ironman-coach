"""FastAPI dependencies."""

from __future__ import annotations

import logging
import os

import jwt
from fastapi import Depends, Header, HTTPException

from api.persistence.store import Store, get_store

logger = logging.getLogger("ironman_coach.auth")


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


def _is_production() -> bool:
    """Return True when running in a production-like environment."""
    env = os.environ.get("ENV", os.environ.get("ENVIRONMENT", "")).lower()
    if env in ("production", "prod", "staging"):
        return True
    if os.environ.get("RENDER") or os.environ.get("FLY_APP_NAME"):
        return True
    # A configured Supabase URL signals a non-local deployment even on
    # custom hosts that don't set the PaaS-specific vars above.
    if os.environ.get("SUPABASE_URL"):
        return True
    return False


def verify_access_token(token: str) -> str:
    """Verify JWT and return auth user id (sub claim)."""
    secret = os.environ.get("SUPABASE_JWT_SECRET")
    if not secret:
        if _is_production():
            logger.error(
                "SUPABASE_JWT_SECRET is not set in a production environment — "
                "rejecting all authenticated requests."
            )
            raise HTTPException(
                status_code=500,
                detail="Server authentication is misconfigured",
            )
        logger.warning(
            "SUPABASE_JWT_SECRET is not set — accepting unverified dev tokens. "
            "Do NOT use this in production."
        )
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
