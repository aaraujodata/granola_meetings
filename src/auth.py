"""Token loading, validation, and refresh for Granola's WorkOS auth."""

import json
import logging
import time

from .config import SUPABASE_JSON

log = logging.getLogger(__name__)


def _read_supabase() -> dict:
    """Read and return the raw supabase.json contents."""
    with open(SUPABASE_JSON, "r") as f:
        return json.load(f)


def _parse_workos_tokens(raw: dict) -> dict:
    """Parse the workos_tokens JSON string from supabase.json."""
    wt = raw.get("workos_tokens", "{}")
    if isinstance(wt, str):
        return json.loads(wt)
    return wt


def load_token() -> str:
    """Load the current access token from supabase.json.

    Returns the raw JWT string.
    Raises FileNotFoundError if supabase.json is missing.
    Raises KeyError if the expected keys are absent.
    """
    raw = _read_supabase()
    tokens = _parse_workos_tokens(raw)
    access_token = tokens["access_token"]
    log.debug("Loaded access token (len=%d)", len(access_token))
    return access_token


def is_token_valid(buffer_seconds: int = 300) -> bool:
    """Check whether the current token is still valid.

    Args:
        buffer_seconds: Safety margin before actual expiry (default 5 min).

    Returns True if the token has not yet expired (minus buffer).
    """
    raw = _read_supabase()
    tokens = _parse_workos_tokens(raw)

    obtained_at_ms = tokens.get("obtained_at", 0)
    expires_in_s = tokens.get("expires_in", 0)

    expiry_ms = obtained_at_ms + (expires_in_s * 1000)
    now_ms = int(time.time() * 1000)
    buffer_ms = buffer_seconds * 1000

    valid = now_ms < (expiry_ms - buffer_ms)
    if not valid:
        remaining_s = (expiry_ms - now_ms) / 1000
        log.warning("Token expires in %.0f seconds (buffer=%ds)", remaining_s, buffer_seconds)
    return valid


def get_headers() -> dict:
    """Return complete HTTP headers for Granola API calls."""
    from .config import GRANOLA_VERSION

    token = load_token()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": f"Granola/{GRANOLA_VERSION}",
        "X-Client-Version": GRANOLA_VERSION,
    }


def get_token_info() -> dict:
    """Return diagnostic info about the current token (no secrets)."""
    raw = _read_supabase()
    tokens = _parse_workos_tokens(raw)

    obtained_at_ms = tokens.get("obtained_at", 0)
    expires_in_s = tokens.get("expires_in", 0)
    expiry_ms = obtained_at_ms + (expires_in_s * 1000)
    now_ms = int(time.time() * 1000)

    return {
        "token_length": len(tokens.get("access_token", "")),
        "expires_in_seconds": expires_in_s,
        "remaining_seconds": (expiry_ms - now_ms) / 1000,
        "has_refresh_token": bool(tokens.get("refresh_token")),
        "is_valid": now_ms < expiry_ms,
    }
