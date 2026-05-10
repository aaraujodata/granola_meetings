"""Shared fixtures for Granola pipeline tests."""

import json
import time

import pytest

from src import auth


def make_supabase_json(*, expires_in=21599, age_seconds=0, refresh_token="test-refresh-tok"):
    """Build a supabase.json dict with controllable token age.

    Args:
        expires_in: Token lifetime in seconds (default ~6h).
        age_seconds: How old the token already is (0 = just obtained).
        refresh_token: Refresh token value (None to omit).
    """
    obtained_at_ms = int((time.time() - age_seconds) * 1000)
    tokens = {
        "access_token": "disk-access-token",
        "expires_in": expires_in,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "obtained_at": obtained_at_ms,
        "session_id": "session_test",
        "external_id": "ext_test",
        "sign_in_method": "GoogleOAuth",
    }
    return {
        "workos_tokens": json.dumps(tokens),
        "session_id": "session_test",
    }


def make_refresh_response(*, access_token="refreshed-access-token", refresh_token="new-refresh-tok"):
    """Build a response dict from the refresh endpoint."""
    return {
        "access_token": access_token,
        "expires_in": 21599,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "obtained_at": int(time.time() * 1000),
        "session_id": "session_refreshed",
        "external_id": "ext_test",
        "sign_in_method": "GoogleOAuth",
    }


@pytest.fixture(autouse=True)
def reset_auth_cache(tmp_path, monkeypatch):
    """Reset the auth cache and isolate tests from host Granola token files."""
    monkeypatch.setattr(auth, "STORED_ACCOUNTS_JSON", tmp_path / "missing-stored-accounts.json")
    auth._reset_cache()
    yield
    auth._reset_cache()
