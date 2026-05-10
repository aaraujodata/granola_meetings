"""Token loading, validation, and refresh for Granola's WorkOS auth.

Granola stores the live WorkOS tokens in `stored-accounts.json` (newer builds).
Older builds wrote tokens to `supabase.json` under the `workos_tokens` key.
We prefer the freshest token set and keep refreshed tokens in memory so long
running jobs can survive access-token expiry.
"""

import json
import logging
import threading
import time

import requests

from .config import BASE_API_URL, GRANOLA_VERSION, STORED_ACCOUNTS_JSON, SUPABASE_JSON

log = logging.getLogger(__name__)

_lock = threading.Lock()


class _TokenCache:
    """In-memory cache for the most recent valid token set."""

    __slots__ = ("access_token", "refresh_token", "obtained_at_ms", "expires_in_s")

    def __init__(self):
        self.access_token: str | None = None
        self.refresh_token: str | None = None
        self.obtained_at_ms: int = 0
        self.expires_in_s: int = 0

    def update(self, tokens: dict) -> None:
        self.access_token = tokens["access_token"]
        self.refresh_token = tokens.get("refresh_token", self.refresh_token)
        self.obtained_at_ms = tokens.get("obtained_at") or int(time.time() * 1000)
        self.expires_in_s = tokens.get("expires_in", 0)

    def is_populated(self) -> bool:
        return self.access_token is not None

    def remaining_seconds(self) -> float:
        expiry_ms = self.obtained_at_ms + (self.expires_in_s * 1000)
        now_ms = int(time.time() * 1000)
        return (expiry_ms - now_ms) / 1000

    def is_valid(self, buffer_seconds: int = 300) -> bool:
        return self.remaining_seconds() > buffer_seconds


_cache = _TokenCache()


def _reset_cache() -> None:
    """Reset the module-level cache. Used by tests."""
    with _lock:
        _cache.access_token = None
        _cache.refresh_token = None
        _cache.obtained_at_ms = 0
        _cache.expires_in_s = 0


def _read_stored_accounts_tokens() -> dict | None:
    """Read WorkOS tokens from `stored-accounts.json`."""
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
    tokens_raw = raw.get("workos_tokens")
    if not tokens_raw:
        return None
    return json.loads(tokens_raw) if isinstance(tokens_raw, str) else tokens_raw


def _read_tokens() -> dict:
    """Return the freshest WorkOS tokens available."""
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


def _read_disk_tokens() -> dict:
    """Compatibility wrapper for tests and older call sites."""
    return _read_tokens()


def _do_refresh(refresh_token: str) -> dict:
    """POST to Granola's refresh endpoint and return the new token dict."""
    resp = requests.post(
        f"{BASE_API_URL}/v1/refresh-access-token",
        json={"refresh_token": refresh_token},
        headers={
            "Content-Type": "application/json",
            "X-Client-Version": GRANOLA_VERSION,
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def load_token() -> str:
    """Load the best available access token, refreshing if needed."""
    with _lock:
        try:
            disk_tokens = _read_disk_tokens()
        except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
            if not _cache.is_populated():
                raise FileNotFoundError(f"Cannot read supabase.json and no cached token: {e}") from e
            disk_tokens = None

        if disk_tokens:
            disk_obtained = disk_tokens.get("obtained_at", 0)
            if disk_obtained > _cache.obtained_at_ms:
                _cache.update(disk_tokens)
                log.debug("Using disk token (obtained_at=%d)", disk_obtained)
            elif _cache.is_populated():
                log.debug("Using cached token (obtained_at=%d)", _cache.obtained_at_ms)
            else:
                _cache.update(disk_tokens)

        if _cache.is_valid():
            return _cache.access_token or ""

        refresh_token = _cache.refresh_token
        if not refresh_token and disk_tokens:
            refresh_token = disk_tokens.get("refresh_token")

        if not refresh_token:
            remaining = _cache.remaining_seconds()
            raise RuntimeError(
                f"Token expired (remaining: {remaining:.0f}s) and no refresh_token available. "
                "Open Granola desktop app to refresh."
            )

        log.info("Token near expiry (%.0fs remaining), attempting refresh...", _cache.remaining_seconds())
        try:
            new_tokens = _do_refresh(refresh_token)
        except Exception as e:
            log.error("Token refresh failed: %s", e)
            raise RuntimeError(
                f"Token expired and refresh failed: {e}. Open Granola desktop app to refresh."
            ) from e

        _cache.update(new_tokens)
        log.info("Token refreshed successfully (new expiry in %.0fm)", _cache.expires_in_s / 60)
        return _cache.access_token or ""


def is_token_valid(buffer_seconds: int = 300) -> bool:
    """Check whether the best available token is still valid without refreshing."""
    with _lock:
        if _cache.is_populated() and _cache.is_valid(buffer_seconds):
            return True

        try:
            disk_tokens = _read_disk_tokens()
        except (FileNotFoundError, KeyError, json.JSONDecodeError):
            return False

        disk_obtained = disk_tokens.get("obtained_at", 0)
        disk_expires = disk_tokens.get("expires_in", 0)
        disk_expiry_ms = disk_obtained + (disk_expires * 1000)
        now_ms = int(time.time() * 1000)
        buffer_ms = buffer_seconds * 1000

        valid = now_ms < (disk_expiry_ms - buffer_ms)
        if valid and disk_obtained > _cache.obtained_at_ms:
            _cache.update(disk_tokens)
        elif not valid:
            remaining_s = (disk_expiry_ms - now_ms) / 1000
            log.warning("Token expires in %.0f seconds (buffer=%ds)", remaining_s, buffer_seconds)
        return valid


def ensure_valid_token() -> str:
    """Ensure we have a valid token, refreshing if needed."""
    return load_token()


def get_headers() -> dict:
    """Return complete HTTP headers for Granola API calls."""
    token = load_token()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": f"Granola/{GRANOLA_VERSION}",
        "X-Client-Version": GRANOLA_VERSION,
    }


def get_token_info() -> dict:
    """Return diagnostic info about the current token without exposing secrets."""
    with _lock:
        try:
            disk_tokens = _read_disk_tokens()
            disk_obtained = disk_tokens.get("obtained_at", 0)
            disk_expires = disk_tokens.get("expires_in", 0)
            disk_expiry_ms = disk_obtained + (disk_expires * 1000)
            now_ms = int(time.time() * 1000)
            disk_remaining = (disk_expiry_ms - now_ms) / 1000
        except (FileNotFoundError, KeyError, json.JSONDecodeError):
            disk_tokens = {}
            disk_expires = 0
            disk_remaining = 0

        using_cache = _cache.is_populated() and _cache.obtained_at_ms >= disk_tokens.get("obtained_at", 0)
        token_length = len(_cache.access_token or disk_tokens.get("access_token", ""))
        return {
            "token_length": token_length,
            "expires_in_seconds": _cache.expires_in_s if using_cache else disk_expires,
            "remaining_seconds": _cache.remaining_seconds() if using_cache else disk_remaining,
            "has_refresh_token": bool(_cache.refresh_token or disk_tokens.get("refresh_token")),
            "is_valid": _cache.is_valid() if using_cache else (disk_remaining > 300),
            "source": "cache" if using_cache else "disk",
        }
