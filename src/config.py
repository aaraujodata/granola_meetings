"""Central configuration for paths, API URLs, and constants."""

from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
GRANOLA_SUPPORT_DIR = Path.home() / "Library" / "Application Support" / "Granola"
SUPABASE_JSON = GRANOLA_SUPPORT_DIR / "supabase.json"
CACHE_V3_JSON = GRANOLA_SUPPORT_DIR / "cache-v3.json"

# Output directories (all relative to repo root)
MEETINGS_DIR = REPO_ROOT / "meetings"
DB_DIR = REPO_ROOT / "db"
EXPORTS_DIR = REPO_ROOT / "exports"

SEARCH_DB_PATH = DB_DIR / "granola_search.db"
EXPORT_PROGRESS_PATH = DB_DIR / "export_progress.json"

# ── API ────────────────────────────────────────────────────────────────────
BASE_API_URL = "https://api.granola.ai"
GRANOLA_VERSION = "5.354.0"

ENDPOINTS = {
    "get_documents": "/v2/get-documents",
    "get_transcript": "/v1/get-document-transcript",
    "get_panels": "/v1/get-document-panels",
    "get_documents_batch": "/v1/get-documents-batch",
    "get_workspaces": "/v1/get-workspaces",
}

# ── Rate limiting ──────────────────────────────────────────────────────────
REQUEST_DELAY_S = 0.1          # 100 ms between API calls
RETRY_MAX_ATTEMPTS = 3
RETRY_BACKOFF_BASE_S = 1.0     # 1s, 2s, 4s exponential backoff

# ── Pagination ─────────────────────────────────────────────────────────────
DOCUMENTS_PAGE_SIZE = 100
