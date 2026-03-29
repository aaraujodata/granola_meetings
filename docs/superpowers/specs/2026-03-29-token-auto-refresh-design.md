# Token Auto-Refresh Design

## Problem

The ARQ worker crashes when the Granola JWT token nears expiry (~6h lifetime). `export_all.py` calls `is_token_valid()` with a 300s buffer and hard-fails, raising an error that kills the worker. There is no automatic refresh — the only recovery is manually opening the Granola desktop app.

A working refresh endpoint exists at `POST https://api.granola.ai/v1/refresh-access-token` that accepts `{refresh_token}` and returns fresh tokens with a new 6h lifetime. This endpoint has been tested and confirmed working.

## Approach: In-Memory Lazy Refresh

Refreshed tokens live only in process memory. No writes to `supabase.json` (Docker mount is `:ro`). On container restart, the process re-reads disk and can refresh again if needed.

## Design

### Token Cache (`src/auth.py`)

Module-level `_TokenCache` class holding:
- `access_token: str`
- `refresh_token: str`
- `obtained_at_ms: int`
- `expires_in_s: int`

Protected by `threading.Lock` (worker runs tasks in thread executors via `run_in_executor`).

### Token Resolution Flow

`load_token()` becomes the single entry point:

1. Read tokens from disk (`supabase.json`) — always, to pick up Granola desktop refreshes
2. Compare disk `obtained_at` vs cache `obtained_at` — use whichever is newer
3. If best token is valid (300s buffer) — return `access_token`
4. If expired but `refresh_token` available — call `_do_refresh()`
5. If refresh succeeds — update cache, return new `access_token`
6. If refresh fails — raise `RuntimeError`

### Refresh Mechanism

```python
def _do_refresh(refresh_token: str) -> dict:
    """POST to Granola refresh endpoint. Returns new token dict."""
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
```

The refresh request includes `X-Client-Version` but NOT `Authorization` — when refreshing, the current access_token may already be expired. Testing confirmed the endpoint works with just the refresh_token in the body.

### Integration Points

**`src/auth.py`** — new/changed functions:
- `load_token()` — rewritten with cache + refresh logic (described above)
- `is_token_valid()` — uses cache when available, still checks disk too
- `ensure_valid_token()` — public function: returns True if token is valid (refreshing if needed), raises RuntimeError if unrecoverable
- `get_headers()` — unchanged, calls `load_token()` which now handles everything
- `get_token_info()` — updated to report cache state

**`src/api_client.py`** — 401 handler change:
```python
if resp.status_code == 401:
    # Force a refresh attempt instead of just re-reading stale disk
    from .auth import ensure_valid_token
    try:
        ensure_valid_token()
    except RuntimeError:
        pass  # will fail on next iteration / max retries
    continue
```

**`scripts/export_all.py`** — pre-flight check:
```python
# Replace hard fail with refresh attempt
from src.auth import ensure_valid_token
ensure_valid_token()  # refreshes if needed, raises if unrecoverable
```

### What Does NOT Change

- `get_headers()` signature and behavior
- `GranolaClient` public API
- Docker mount configuration (stays `:ro`)
- Worker task functions (they already catch exceptions properly after the earlier fix)
- The 300s buffer value

## Test Plan

New `tests/` directory. pytest with mocked HTTP (no real API calls).

### `tests/test_auth.py`

| Test | What it verifies |
|------|-----------------|
| `test_load_token_from_disk` | Cold start loads from supabase.json |
| `test_cache_preferred_over_stale_disk` | Cached token with newer obtained_at wins |
| `test_disk_preferred_over_stale_cache` | Disk token wins when Granola desktop refreshed |
| `test_auto_refresh_on_near_expiry` | Expired token triggers refresh endpoint call |
| `test_refresh_updates_cache` | After refresh, subsequent load_token returns new token |
| `test_refresh_failure_raises` | HTTP error from refresh endpoint raises RuntimeError |
| `test_refresh_not_called_when_valid` | Valid token skips refresh entirely |
| `test_thread_safety` | Concurrent load_token calls don't corrupt cache |
| `test_ensure_valid_token_refreshes` | ensure_valid_token triggers refresh when needed |
| `test_ensure_valid_token_raises_on_failure` | ensure_valid_token raises when refresh fails |
| `test_is_token_valid_uses_cache` | is_token_valid checks cache, not just disk |

### `tests/test_api_client.py`

| Test | What it verifies |
|------|-----------------|
| `test_401_triggers_refresh_then_retries` | 401 response calls ensure_valid_token and retries |
| `test_401_with_failed_refresh_exhausts_retries` | Unrecoverable 401 raises GranolaAPIError |

### Test infrastructure

- `pytest` added to requirements
- `conftest.py` with fixtures for mock supabase.json and cache reset
- All tests use `unittest.mock.patch` / `monkeypatch` for HTTP and file I/O
