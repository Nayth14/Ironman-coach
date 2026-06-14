"""Auth API integration tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app
from tests.auth_helpers import make_token, reset_store


def test_protected_route_requires_auth(monkeypatch, tmp_path):
    reset_store(monkeypatch, tmp_path)
    client = TestClient(app)
    res = client.get("/api/plans/current")
    assert res.status_code == 401


def test_guest_onboarding_still_public(monkeypatch, tmp_path):
    reset_store(monkeypatch, tmp_path)
    client = TestClient(app)
    res = client.post("/api/guests", json={})
    assert res.status_code == 200
    assert "guestId" in res.json()


def test_link_guest_flow(monkeypatch, tmp_path):
    reset_store(monkeypatch, tmp_path)
    client = TestClient(app)

    guest_res = client.post("/api/guests", json={})
    guest_id = guest_res.json()["guestId"]
    token = make_token("auth-user-99", secret=None)

    link_res = client.post(
        "/api/auth/link-guest",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Guest-Id": guest_id,
        },
    )
    assert link_res.status_code == 200
    body = link_res.json()
    assert body["linked"] is True
    assert body["athleteId"]

    me_res = client.get(
        "/api/plans/current",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 404


def test_link_guest_conflict(monkeypatch, tmp_path):
    reset_store(monkeypatch, tmp_path)
    client = TestClient(app)

    guest_a = client.post("/api/guests", json={}).json()["guestId"]
    guest_b = client.post("/api/guests", json={}).json()["guestId"]
    token = make_token("shared-auth", secret=None)

    first = client.post(
        "/api/auth/link-guest",
        headers={"Authorization": f"Bearer {token}", "X-Guest-Id": guest_a},
    )
    assert first.status_code == 200

    conflict = client.post(
        "/api/auth/link-guest",
        headers={"Authorization": f"Bearer {token}", "X-Guest-Id": guest_b},
    )
    assert conflict.status_code == 409
