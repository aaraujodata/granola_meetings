"""Token loading, validation, and refresh for Granola's WorkOS auth."""

import json
import logging
import threading
import time

import requests

from .config import BASE_API_URL, GRANOLA_VERSION, SUPABASE_JSON

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Token cache — holds refreshed tokens in memory so we survive token expiry
# without needing the Granola desktop app to be open.
# ---------------------------------------------------------------------------

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
        self.obtained_at_ms = tokens.get("obtained_at", 0)
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


# ---------------------------------------------------------------------------
# Disk I/O — read supabase.json
# ---------------------------------------------------------------------------

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


def _read_disk_tokens() -> dict:
    """Read and parse token dict from supabase.json."""
    raw = _read_supabase()
    return _parse_workos_tokens(raw)


# ---------------------------------------------------------------------------
# Refresh — call Granola's refresh endpoint
# ---------------------------------------------------------------------------

def _do_refresh(refresh_token: str) -> dict:
    """POST to Granola's refresh endpoint. Returns new token dict.

    Raises requests.HTTPError on failure.
    """
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


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_token() -> str:
    """Load the best available access token (cache > disk), refreshing if needed.

    Resolution order:
    1. Read disk tokens (picks up Granola desktop refreshes)
    2. Compare disk vs cache — use whichever has later obtained_at
    3. If best token is valid → return it
    4. If expired → attempt refresh
    5. If refresh fails → raise RuntimeError
    """
    with _lock:
        # Step 1: read disk
        try:
            disk_tokens = _read_disk_tokens()
        except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
            if not _cache.is_populated():
                raise FileNotFoundError(f"Cannot read supabase.json and no cached token: {e}") from e
            disk_tokens = None

        # Step 2: pick the fresher token source
        if disk_tokens:
            disk_obtained = disk_tokens.get("obtained_at", 0)
            if disk_obtained > _cache.obtained_at_ms:
                _cache.update(disk_tokens)
                log.debug("Using disk token (obtained_at=%d)", disk_obtained)
            elif _cache.is_populated():
                log.debug("Using cached token (obtained_at=%d)", _cache.obtained_at_ms)
            else:
                _cache.update(disk_tokens)

        # Step 3: check validity
        if _cache.is_valid():
            return _cache.access_token

        # Step 4: attempt refresh
        refresh_tok = _cache.refresh_token
        if not refresh_tok and disk_tokens:
            refresh_tok = disk_tokens.get("refresh_token")

        if not refresh_tok:
            remaining = _cache.remaining_seconds()
            raise RuntimeError(
                f"Token expired (remaining: {remaining:.0f}s) and no refresh_token available. "
                "Open Granola desktop app to refresh."
            )

        log.info("Token near expiry (%.0fs remaining), attempting refresh...", _cache.remaining_seconds())

    # Release lock during network call to avoid blocking other threads
    try:
        new_tokens = _do_refresh(refresh_tok)
    except Exception as e:
        log.error("Token refresh failed: %s", e)
        raise RuntimeError(
            f"Token expired and refresh failed: {e}. Open Granola desktop app to refresh."
        ) from e

    with _lock:
        _cache.update(new_tokens)
        log.info("Token refreshed successfully (new expiry in %.0fm)", _cache.expires_in_s / 60)
        return _cache.access_token


def is_token_valid(buffer_seconds: int = 300) -> bool:
    """Check whether the best available token is still valid.

    Checks cache first (may have a refreshed token), falls back to disk.
    Does NOT attempt refresh — use ensure_valid_token() for that.
    """
    with _lock:
        # Check cache first
        if _cache.is_populated() and _cache.is_valid(buffer_seconds):
            return True

        # Fall back to disk
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
    """Ensure we have a valid token, refreshing if needed.

    Returns the valid access token.
    Raises RuntimeError if token is unrecoverable.
    """
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
    """Return diagnostic info about the current token (no secrets)."""
    with _lock:
        # Read disk for comparison
        try:
            disk_tokens = _read_disk_tokens()
            disk_obtained = disk_tokens.get("obtained_at", 0)
            disk_expires = disk_tokens.get("expires_in", 0)
            disk_expiry_ms = disk_obtained + (disk_expires * 1000)
            now_ms = int(time.time() * 1000)
            disk_remaining = (disk_expiry_ms - now_ms) / 1000
        except (FileNotFoundError, KeyError, json.JSONDecodeError):
            disk_remaining = 0
            disk_expires = 0
            disk_tokens = {}

        return {
            "token_length": len(_cache.access_token or ""),
            "expires_in_seconds": _cache.expires_in_s if _cache.is_populated() else disk_expires,
            "remaining_seconds": _cache.remaining_seconds() if _cache.is_populated() else disk_remaining,
            "has_refresh_token": bool(_cache.refresh_token or disk_tokens.get("refresh_token")),
            "is_valid": _cache.is_valid() if _cache.is_populated() else (disk_remaining > 300),
            "source": "cache" if _cache.is_populated() and _cache.obtained_at_ms >= disk_tokens.get("obtained_at", 0) else "disk",
        }
