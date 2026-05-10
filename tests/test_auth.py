"""Tests for src/auth.py — token loading, caching, and auto-refresh."""

import json
import threading
import time
from unittest.mock import MagicMock, patch

import pytest
import requests

from src import auth
from tests.conftest import make_refresh_response, make_supabase_json


# ---------------------------------------------------------------------------
# load_token — disk loading
# ---------------------------------------------------------------------------

class TestLoadTokenFromDisk:
    """Cold start: no cache, loads from supabase.json."""

    def test_returns_access_token(self, tmp_path, monkeypatch):
        supabase = make_supabase_json(age_seconds=0)
        f = tmp_path / "supabase.json"
        f.write_text(json.dumps(supabase))
        monkeypatch.setattr(auth, "SUPABASE_JSON", f)

        token = auth.load_token()
        assert token == "disk-access-token"

    def test_raises_when_file_missing_and_no_cache(self, tmp_path, monkeypatch):
        monkeypatch.setattr(auth, "SUPABASE_JSON", tmp_path / "missing.json")

        with pytest.raises(FileNotFoundError, match="Cannot read supabase.json"):
            auth.load_token()

    def test_populates_cache_on_first_load(self, tmp_path, monkeypatch):
        supabase = make_supabase_json(age_seconds=0)
        f = tmp_path / "supabase.json"
        f.write_text(json.dumps(supabase))
        monkeypatch.setattr(auth, "SUPABASE_JSON", f)

        auth.load_token()
        assert auth._cache.is_populated()
        assert auth._cache.access_token == "disk-access-token"


# ---------------------------------------------------------------------------
# load_token — cache vs disk freshness
# ---------------------------------------------------------------------------

class TestCacheVsDiskFreshness:
    """The fresher token source (by obtained_at) wins."""

    def test_cache_preferred_over_stale_disk(self, tmp_path, monkeypatch):
        # Disk token: obtained 1 hour ago
        supabase = make_supabase_json(age_seconds=3600)
        f = tmp_path / "supabase.json"
        f.write_text(json.dumps(supabase))
        monkeypatch.setattr(auth, "SUPABASE_JSON", f)

        # Pre-populate cache with a newer token
        auth._cache.access_token = "cached-access-token"
        auth._cache.refresh_token = "cached-refresh"
        auth._cache.obtained_at_ms = int(time.time() * 1000)  # just now
        auth._cache.expires_in_s = 21599

        token = auth.load_token()
        assert token == "cached-access-token"

    def test_disk_preferred_over_stale_cache(self, tmp_path, monkeypatch):
        # Disk token: just obtained
        supabase = make_supabase_json(age_seconds=0)
        f = tmp_path / "supabase.json"
        f.write_text(json.dumps(supabase))
        monkeypatch.setattr(auth, "SUPABASE_JSON", f)

        # Pre-populate cache with an older token
        auth._cache.access_token = "old-cached-token"
        auth._cache.refresh_token = "old-refresh"
        auth._cache.obtained_at_ms = int((time.time() - 7200) * 1000)  # 2h ago
        auth._cache.expires_in_s = 21599

        token = auth.load_token()
        assert token == "disk-access-token"


# ---------------------------------------------------------------------------
# load_token — auto-refresh
# ---------------------------------------------------------------------------

class TestAutoRefresh:
    """When token is near-expiry, load_token calls the refresh endpoint."""

    def test_refresh_triggered_on_near_expiry(self, tmp_path, monkeypatch):
        # Token that's almost expired (only 100s left, under 300s buffer)
        supabase = make_supabase_json(age_seconds=21599 - 100)
        f = tmp_path / "supabase.json"
        f.write_text(json.dumps(supabase))
        monkeypatch.setattr(auth, "SUPABASE_JSON", f)

        refresh_resp = make_refresh_response()
        with patch.object(auth, "_do_refresh", return_value=refresh_resp) as mock_refresh:
            token = auth.load_token()

        mock_refresh.assert_called_once_with("test-refresh-tok")
        assert token == "refreshed-access-token"

    def test_refresh_updates_cache(self, tmp_path, monkeypatch):
        supabase = make_supabase_json(age_seconds=21599 - 100)
        f = tmp_path / "supabase.json"
        f.write_text(json.dumps(supabase))
        monkeypatch.setattr(auth, "SUPABASE_JSON", f)

        refresh_resp = make_refresh_response(
            access_token="fresh-token",
            refresh_token="fresh-refresh",
        )
        with patch.object(auth, "_do_refresh", return_value=refresh_resp):
            auth.load_token()

        assert auth._cache.access_token == "fresh-token"
        assert auth._cache.refresh_token == "fresh-refresh"
        assert auth._cache.is_valid()

    def test_refresh_not_called_when_valid(self, tmp_path, monkeypatch):
        supabase = make_supabase_json(age_seconds=0)  # fresh token
        f = tmp_path / "supabase.json"
        f.write_text(json.dumps(supabase))
        monkeypatch.setattr(auth, "SUPABASE_JSON", f)

        with patch.object(auth, "_do_refresh") as mock_refresh:
            auth.load_token()

        mock_refresh.assert_not_called()

    def test_refresh_failure_raises(self, tmp_path, monkeypatch):
        supabase = make_supabase_json(age_seconds=21599 - 100)
        f = tmp_path / "supabase.json"
        f.write_text(json.dumps(supabase))
        monkeypatch.setattr(auth, "SUPABASE_JSON", f)

        with patch.object(auth, "_do_refresh", side_effect=requests.HTTPError("403 Forbidden")):
            with pytest.raises(RuntimeError, match="refresh failed"):
                auth.load_token()

    def test_no_refresh_token_raises(self, tmp_path, monkeypatch):
        supabase = make_supabase_json(age_seconds=21599 - 100, refresh_token=None)
        f = tmp_path / "supabase.json"
        f.write_text(json.dumps(supabase))
        monkeypatch.setattr(auth, "SUPABASE_JSON", f)

        with pytest.raises(RuntimeError, match="no refresh_token available"):
            auth.load_token()


# ---------------------------------------------------------------------------
# is_token_valid
# ---------------------------------------------------------------------------

class TestIsTokenValid:
    def test_valid_disk_token(self, tmp_path, monkeypatch):
        supabase = make_supabase_json(age_seconds=0)
        f = tmp_path / "supabase.json"
        f.write_text(json.dumps(supabase))
        monkeypatch.setattr(auth, "SUPABASE_JSON", f)

        assert auth.is_token_valid() is True

    def test_expired_disk_token(self, tmp_path, monkeypatch):
        supabase = make_supabase_json(age_seconds=21599 - 100)
        f = tmp_path / "supabase.json"
        f.write_text(json.dumps(supabase))
        monkeypatch.setattr(auth, "SUPABASE_JSON", f)

        assert auth.is_token_valid() is False

    def test_uses_cache_when_populated(self, tmp_path, monkeypatch):
        # Disk token is expired
        supabase = make_supabase_json(age_seconds=22000)
        f = tmp_path / "supabase.json"
        f.write_text(json.dumps(supabase))
        monkeypatch.setattr(auth, "SUPABASE_JSON", f)

        # But cache has a valid token
        auth._cache.access_token = "cached-valid"
        auth._cache.refresh_token = "r"
        auth._cache.obtained_at_ms = int(time.time() * 1000)
        auth._cache.expires_in_s = 21599

        assert auth.is_token_valid() is True


# ---------------------------------------------------------------------------
# ensure_valid_token
# ---------------------------------------------------------------------------

class TestEnsureValidToken:
    def test_returns_token_when_valid(self, tmp_path, monkeypatch):
        supabase = make_supabase_json(age_seconds=0)
        f = tmp_path / "supabase.json"
        f.write_text(json.dumps(supabase))
        monkeypatch.setattr(auth, "SUPABASE_JSON", f)

        token = auth.ensure_valid_token()
        assert token == "disk-access-token"

    def test_refreshes_when_expired(self, tmp_path, monkeypatch):
        supabase = make_supabase_json(age_seconds=21599 - 100)
        f = tmp_path / "supabase.json"
        f.write_text(json.dumps(supabase))
        monkeypatch.setattr(auth, "SUPABASE_JSON", f)

        refresh_resp = make_refresh_response()
        with patch.object(auth, "_do_refresh", return_value=refresh_resp):
            token = auth.ensure_valid_token()
        assert token == "refreshed-access-token"

    def test_raises_on_unrecoverable(self, tmp_path, monkeypatch):
        supabase = make_supabase_json(age_seconds=21599 - 100)
        f = tmp_path / "supabase.json"
        f.write_text(json.dumps(supabase))
        monkeypatch.setattr(auth, "SUPABASE_JSON", f)

        with patch.object(auth, "_do_refresh", side_effect=requests.HTTPError("fail")):
            with pytest.raises(RuntimeError):
                auth.ensure_valid_token()


# ---------------------------------------------------------------------------
# Thread safety
# ---------------------------------------------------------------------------

class TestThreadSafety:
    def test_concurrent_load_token(self, tmp_path, monkeypatch):
        """Multiple threads calling load_token don't corrupt the cache."""
        supabase = make_supabase_json(age_seconds=0)
        f = tmp_path / "supabase.json"
        f.write_text(json.dumps(supabase))
        monkeypatch.setattr(auth, "SUPABASE_JSON", f)

        results = []
        errors = []

        def worker():
            try:
                token = auth.load_token()
                results.append(token)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert len(results) == 20
        assert all(t == "disk-access-token" for t in results)

    def test_concurrent_refresh(self, tmp_path, monkeypatch):
        """When token expires, only one refresh call should succeed and all threads get the result."""
        supabase = make_supabase_json(age_seconds=21599 - 100)
        f = tmp_path / "supabase.json"
        f.write_text(json.dumps(supabase))
        monkeypatch.setattr(auth, "SUPABASE_JSON", f)

        call_count = 0
        refresh_resp = make_refresh_response()

        original_do_refresh = auth._do_refresh

        def counting_refresh(refresh_token):
            nonlocal call_count
            call_count += 1
            time.sleep(0.05)  # simulate network delay
            return refresh_resp

        results = []
        errors = []

        def worker():
            try:
                token = auth.load_token()
                results.append(token)
            except Exception as e:
                errors.append(e)

        with patch.object(auth, "_do_refresh", side_effect=counting_refresh):
            threads = [threading.Thread(target=worker) for _ in range(10)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

        assert not errors
        assert len(results) == 10
        assert all(t == "refreshed-access-token" for t in results)


# ---------------------------------------------------------------------------
# _do_refresh — unit test the HTTP call
# ---------------------------------------------------------------------------

class TestDoRefresh:
    def test_calls_correct_endpoint(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = make_refresh_response()

        with patch("src.auth.requests.post", return_value=mock_resp) as mock_post:
            result = auth._do_refresh("my-refresh-token")

        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert "/v1/refresh-access-token" in call_kwargs.args[0]
        assert call_kwargs.kwargs["json"] == {"refresh_token": "my-refresh-token"}
        assert result["access_token"] == "refreshed-access-token"

    def test_raises_on_http_error(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.raise_for_status.side_effect = requests.HTTPError("401 Unauthorized")

        with patch("src.auth.requests.post", return_value=mock_resp):
            with pytest.raises(requests.HTTPError):
                auth._do_refresh("bad-token")
