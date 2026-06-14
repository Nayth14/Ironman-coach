"""Auth test helpers."""

from __future__ import annotations

import base64
import json
import time

import jwt

import api.persistence.store as store_module


def reset_store(monkeypatch, tmp_path):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_JWT_SECRET", raising=False)
    monkeypatch.setattr(store_module, "_DB_PATH", tmp_path / "test.db")
    store_module._store = None


def make_token(
    sub: str = "auth-user-1",
    *,
    secret: str | None = "test-secret",
    exp_offset: int = 3600,
    audience: str = "authenticated",
) -> str:
    payload = {
        "sub": sub,
        "aud": audience,
        "exp": int(time.time()) + exp_offset,
    }
    if secret:
        return jwt.encode(payload, secret, algorithm="HS256")
    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode().rstrip("=")
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    return f"{header}.{body}.unsigned"
