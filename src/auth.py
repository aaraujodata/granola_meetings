"""Token loading, validation, and refresh for Granola's WorkOS auth.

Granola stores the live WorkOS tokens in `stored-accounts.json` (newer builds).
Older builds wrote tokens to `supabase.json` under the `workos_tokens` key.
We prefer `stored-accounts.json` and fall back to `supabase.json`.
"""

import json
import logging
import time

from .config import STORED_ACCOUNTS_JSON, SUPABASE_JSON

log = logging.getLogger(__name__)


def _read_stored_accounts_tokens() -> dict | None:
    """Read WorkOS tokens from `stored-accounts.json` (current Granola location).

    Returns the parsed tokens dict, or None if the file is absent / has no accounts.
    """
    if not STORED_ACCOUNTS_JSON.exists():
        return None
    with open(STORED_ACCOUNTS_JSON, "r") as f:
        outer = json.load(f)
    accounts_raw = outer.get("accounts")
    if not accounts_raw:
        return None
    accounts = json.loads(accounts_raw) if isinstance(accounts_raw, str) else accounts_raw
    if not accounts:
        return None
    # Pick the most recently saved account.
    account = max(accounts, key=lambda a: a.get("savedAt", 0))
    tokens_raw = account.get("tokens")
    if not tokens_raw:
        return None
    return json.loads(tokens_raw) if isinstance(tokens_raw, str) else tokens_raw


def _read_supabase_tokens() -> dict | None:
    """Read WorkOS tokens from legacy `supabase.json`."""
    if not SUPABASE_JSON.exists():
        return None
    with open(SUPABASE_JSON, "r") as f:
        raw = json.load(f)
    wt = raw.get("workos_tokens")
    if not wt:
        return None
    return json.loads(wt) if isinstance(wt, str) else wt


def _read_tokens() -> dict:
    """Return the freshest WorkOS tokens available, preferring stored-accounts.json.

    If both files exist, the one with the larger `obtained_at` wins so we never
    fall back to a stale legacy file when the current one is newer.
    """
    new = _read_stored_accounts_tokens()
    old = _read_supabase_tokens()
    if new and old:
        return new if new.get("obtained_at", 0) >= old.get("obtained_at", 0) else old
    if new:
        return new
    if old:
        return old
    raise FileNotFoundError(
        f"No Granola token file found at {STORED_ACCOUNTS_JSON} or {SUPABASE_JSON}"
    )


def load_token() -> str:
    """Load the current access token. Returns the raw JWT string."""
    tokens = _read_tokens()
    access_token = tokens["access_token"]
    log.debug("Loaded access token (len=%d)", len(access_token))
    return access_token


def is_token_valid(buffer_seconds: int = 300) -> bool:
    """Check whether the current token is still valid (with safety buffer)."""
    tokens = _read_tokens()

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
    tokens = _read_tokens()

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
