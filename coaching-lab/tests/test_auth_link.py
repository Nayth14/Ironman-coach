"""Guest-to-auth linking tests."""

from __future__ import annotations

import pytest

from api.persistence.store import Store, get_store
from tests.auth_helpers import reset_store


@pytest.fixture
def store(monkeypatch, tmp_path):
    reset_store(monkeypatch, tmp_path)
    return get_store()


def test_link_guest_to_auth_success(store: Store):
    guest = store.create_guest()
    athlete_id = store.link_guest_to_auth(guest["guest_id"], "auth-1")
    assert athlete_id == guest["id"]
    linked = store.get_athlete_by_auth_user("auth-1")
    assert linked is not None
    assert linked["id"] == guest["id"]


def test_link_guest_to_auth_idempotent(store: Store):
    guest = store.create_guest()
    first = store.link_guest_to_auth(guest["guest_id"], "auth-1")
    second = store.link_guest_to_auth(guest["guest_id"], "auth-1")
    assert first == second


def test_link_guest_to_auth_conflict(store: Store):
    guest_a = store.create_guest()
    guest_b = store.create_guest()
    store.link_guest_to_auth(guest_a["guest_id"], "auth-1")

    with pytest.raises(Store.AuthLinkConflictError):
        store.link_guest_to_auth(guest_b["guest_id"], "auth-1")


def test_link_guest_to_auth_guest_not_found(store: Store):
    with pytest.raises(Store.GuestNotFoundError):
        store.link_guest_to_auth("missing-guest", "auth-1")
