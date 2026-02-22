# Granola Authentication Mechanism

## Token Location

```
~/Library/Application Support/Granola/supabase.json
```

## File Structure

The file contains 4 top-level keys, all stored as strings (some are JSON-encoded):

```json
{
  "cognito_tokens": "<json-string, len ~4070>",
  "user_info": "<json-string, len ~457>",
  "workos_tokens": "<json-string>",
  "session_id": "session_01K2M3VHY7SHHFA9A6CJFVK1JW"
}
```

## workos_tokens (primary auth)

JSON string that must be parsed. Contains:

| Key | Type | Description |
|-----|------|-------------|
| `access_token` | string (len ~881) | JWT Bearer token for API calls |
| `expires_in` | int (21599) | Token lifetime in seconds (~6 hours) |
| `refresh_token` | string (len 25) | For token renewal |
| `token_type` | string | Always "Bearer" |
| `obtained_at` | int | Unix timestamp in **milliseconds** |
| `session_id` | string | WorkOS session ID |
| `external_id` | string | External user identifier |

## Token Validation

```python
import time

obtained_at_ms = workos_tokens["obtained_at"]  # e.g. 1771787723525
expires_in_s = workos_tokens["expires_in"]      # e.g. 21599

# Token is valid if:
current_time_ms = int(time.time() * 1000)
expiry_ms = obtained_at_ms + (expires_in_s * 1000)
is_valid = current_time_ms < expiry_ms

# Add 5-minute buffer for safety:
is_valid_safe = current_time_ms < (expiry_ms - 300_000)
```

## Token Refresh

The Granola app uses WorkOS AuthKit for OAuth. Refresh flow:

```
POST https://api.workos.com/user_management/authenticate
Content-Type: application/json

{
  "grant_type": "refresh_token",
  "client_id": "<workos_client_id>",
  "refresh_token": "<refresh_token>"
}
```

**Note:** The WorkOS client_id is embedded in the Granola app binary. For automation, the simplest approach is to re-open Granola desktop app which refreshes the token automatically.

## user_info Structure

```json
{
  "id": "0ef6bb2c-cbd5-4437-84dc-9d14ec632e18",
  "email": "aaraujo@consumertrack.com",
  "user_metadata": {
    "name": "Alexis",
    "picture": "https://workoscdn.com/...",
    "hd": "consumertrack.com"
  },
  "signed_in_on_platforms": {
    "macos": true,
    "windows": false,
    "ios": true
  },
  "created_at": "2025-01-20T15:01:28..."
}
```

## Required API Headers

```python
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
    "User-Agent": "Granola/5.354.0",
    "X-Client-Version": "5.354.0"
}
```

## Security Notes

- Token file is readable only by the current user (macOS file permissions)
- Never commit supabase.json or tokens to git
- Token lifetime ~6 hours; plan for refresh during long-running exports
