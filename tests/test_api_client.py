"""Tests for src/api_client.py — 401 retry with token refresh."""

import json
import time
from unittest.mock import MagicMock, patch

import pytest
import requests

from src import auth
from src.api_client import GranolaAPIError, GranolaClient
from tests.conftest import make_refresh_response, make_supabase_json


@pytest.fixture
def client_with_valid_token(tmp_path, monkeypatch):
    """Provide a GranolaClient with a valid disk token."""
    supabase = make_supabase_json(age_seconds=0)
    f = tmp_path / "supabase.json"
    f.write_text(json.dumps(supabase))
    monkeypatch.setattr(auth, "SUPABASE_JSON", f)
    return GranolaClient()


class TestRetryOn401:
    def test_401_triggers_refresh_then_retries(self, client_with_valid_token):
        """On 401, ensure_valid_token is called and the request is retried."""
        client = client_with_valid_token

        # First call returns 401, second returns 200
        resp_401 = MagicMock()
        resp_401.status_code = 401
        resp_401.text = "Unauthorized"

        resp_200 = MagicMock()
        resp_200.status_code = 200
        resp_200.json.return_value = {"docs": []}

        with patch.object(client._session, "post", side_effect=[resp_401, resp_200]):
            with patch("src.api_client.ensure_valid_token") as mock_ensure:
                result = client._post("/v2/get-documents", {"limit": 10})

        mock_ensure.assert_called_once()
        assert result.status_code == 200

    def test_401_with_failed_refresh_exhausts_retries(self, client_with_valid_token):
        """When refresh fails and all retries return 401, raises GranolaAPIError."""
        client = client_with_valid_token

        resp_401 = MagicMock()
        resp_401.status_code = 401
        resp_401.text = "Unauthorized"

        with patch.object(client._session, "post", return_value=resp_401):
            with patch("src.api_client.ensure_valid_token", side_effect=RuntimeError("refresh failed")):
                with pytest.raises(GranolaAPIError, match="Max retries"):
                    client._post("/v2/get-documents", {"limit": 10})

    def test_successful_request_no_refresh(self, client_with_valid_token):
        """200 responses don't trigger refresh."""
        client = client_with_valid_token

        resp_200 = MagicMock()
        resp_200.status_code = 200
        resp_200.json.return_value = {"docs": []}

        with patch.object(client._session, "post", return_value=resp_200):
            with patch("src.api_client.ensure_valid_token") as mock_ensure:
                client._post("/v2/get-documents", {"limit": 10})

        mock_ensure.assert_not_called()
