"""Granola internal API client with rate limiting and retry logic."""

import logging
import time

import requests

from .auth import get_headers, is_token_valid, load_token
from .config import (
    BASE_API_URL,
    DOCUMENTS_PAGE_SIZE,
    ENDPOINTS,
    GRANOLA_VERSION,
    REQUEST_DELAY_S,
    RETRY_BACKOFF_BASE_S,
    RETRY_MAX_ATTEMPTS,
)
from .models import GranolaDocument, Panel, TranscriptEntry

log = logging.getLogger(__name__)


class GranolaAPIError(Exception):
    """Raised on non-recoverable API errors."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"HTTP {status_code}: {message}")


class GranolaClient:
    """Wrapper around Granola's internal API endpoints."""

    def __init__(self):
        self._session = requests.Session()
        self._last_request_time = 0.0

    def _ensure_headers(self):
        """Refresh session headers (re-loads token each time for freshness)."""
        self._session.headers.update({
            "Authorization": f"Bearer {load_token()}",
            "Content-Type": "application/json",
            "User-Agent": f"Granola/{GRANOLA_VERSION}",
            "X-Client-Version": GRANOLA_VERSION,
        })

    def _rate_limit(self):
        """Enforce minimum delay between API calls."""
        elapsed = time.time() - self._last_request_time
        if elapsed < REQUEST_DELAY_S:
            time.sleep(REQUEST_DELAY_S - elapsed)

    def _post(self, endpoint: str, payload: dict) -> requests.Response:
        """POST with rate limiting, retry on 429, re-auth on 401."""
        url = f"{BASE_API_URL}{endpoint}"

        for attempt in range(RETRY_MAX_ATTEMPTS):
            self._rate_limit()
            self._ensure_headers()

            resp = self._session.post(url, json=payload)
            self._last_request_time = time.time()

            if resp.status_code == 200:
                return resp

            if resp.status_code == 401:
                log.warning("Got 401 — token may have expired. Retrying with fresh token...")
                # Token is re-loaded on next _ensure_headers() call
                time.sleep(1)
                continue

            if resp.status_code == 429:
                wait = RETRY_BACKOFF_BASE_S * (2 ** attempt)
                log.warning("Rate limited (429). Waiting %.1fs before retry %d/%d",
                            wait, attempt + 1, RETRY_MAX_ATTEMPTS)
                time.sleep(wait)
                continue

            raise GranolaAPIError(resp.status_code, resp.text[:500])

        raise GranolaAPIError(resp.status_code, f"Max retries ({RETRY_MAX_ATTEMPTS}) exceeded")

    # ── Document endpoints ─────────────────────────────────────────────────

    def get_documents_page(self, limit: int = DOCUMENTS_PAGE_SIZE, offset: int = 0) -> dict:
        """Fetch a single page of documents.

        Returns raw response dict with 'docs' and 'deleted' keys.
        """
        resp = self._post(ENDPOINTS["get_documents"], {
            "limit": limit,
            "offset": offset,
            "include_last_viewed_panel": False,
        })
        return resp.json()

    def get_all_documents(self) -> list[GranolaDocument]:
        """Fetch ALL documents across all pages.

        Returns list of GranolaDocument dataclasses.
        """
        all_docs = []
        offset = 0

        while True:
            log.info("Fetching documents page offset=%d limit=%d", offset, DOCUMENTS_PAGE_SIZE)
            data = self.get_documents_page(limit=DOCUMENTS_PAGE_SIZE, offset=offset)
            docs = data.get("docs", [])

            if not docs:
                break

            for raw_doc in docs:
                all_docs.append(GranolaDocument.from_api(raw_doc))

            log.info("  Got %d documents (total so far: %d)", len(docs), len(all_docs))

            if len(docs) < DOCUMENTS_PAGE_SIZE:
                break
            offset += DOCUMENTS_PAGE_SIZE

        log.info("Total documents fetched: %d", len(all_docs))
        return all_docs

    # ── Transcript endpoint ────────────────────────────────────────────────

    def get_transcript(self, document_id: str) -> list[TranscriptEntry]:
        """Fetch transcript entries for a document.

        Returns list of TranscriptEntry (empty if no transcript exists).
        """
        resp = self._post(ENDPOINTS["get_transcript"], {"document_id": document_id})
        raw_entries = resp.json()

        if not isinstance(raw_entries, list):
            log.warning("Unexpected transcript response type for %s: %s",
                        document_id, type(raw_entries).__name__)
            return []

        return [TranscriptEntry.from_api(e) for e in raw_entries]

    # ── Panels endpoint ────────────────────────────────────────────────────

    def get_panels(self, document_id: str) -> list[Panel]:
        """Fetch AI-generated summary panels for a document."""
        resp = self._post(ENDPOINTS["get_panels"], {"document_id": document_id})
        raw_panels = resp.json()

        if not isinstance(raw_panels, list):
            log.warning("Unexpected panels response type for %s: %s",
                        document_id, type(raw_panels).__name__)
            return []

        return [Panel.from_api(p) for p in raw_panels]

    # ── Batch endpoint ─────────────────────────────────────────────────────

    def get_documents_batch(self, document_ids: list[str]) -> list[GranolaDocument]:
        """Fetch multiple documents by ID."""
        resp = self._post(ENDPOINTS["get_documents_batch"], {"document_ids": document_ids})
        data = resp.json()
        docs = data.get("docs", [])
        return [GranolaDocument.from_api(d) for d in docs]

    # ── Workspaces endpoint ────────────────────────────────────────────────

    def get_workspaces(self) -> dict:
        """Fetch workspace information."""
        resp = self._post(ENDPOINTS["get_workspaces"], {})
        return resp.json()
