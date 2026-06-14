"""JWT verification tests."""

from __future__ import annotations

import time

import jwt
import pytest
from fastapi import HTTPException

from api.deps import verify_access_token
from tests.auth_helpers import make_token


def test_verify_access_token_valid(monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "test-secret")
    token = make_token("user-123", secret="test-secret")
    assert verify_access_token(token) == "user-123"


def test_verify_access_token_expired(monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "test-secret")
    token = make_token("user-123", secret="test-secret", exp_offset=-60)
    with pytest.raises(HTTPException) as exc:
        verify_access_token(token)
    assert exc.value.status_code == 401


def test_verify_access_token_invalid_signature(monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "test-secret")
    token = make_token("user-123", secret="other-secret")
    with pytest.raises(HTTPException) as exc:
        verify_access_token(token)
    assert exc.value.status_code == 401


def test_verify_access_token_dev_bypass_without_secret(monkeypatch):
    monkeypatch.delenv("SUPABASE_JWT_SECRET", raising=False)
    token = make_token("dev-user", secret=None)
    assert verify_access_token(token) == "dev-user"


def test_verify_access_token_missing_sub(monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "test-secret")
    payload = {"aud": "authenticated", "exp": int(time.time()) + 3600}
    token = jwt.encode(payload, "test-secret", algorithm="HS256")
    with pytest.raises(HTTPException) as exc:
        verify_access_token(token)
    assert exc.value.status_code == 401
