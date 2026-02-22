"""Status router: token, database, and export stats."""

import json
from pathlib import Path

from fastapi import APIRouter

from app.dependencies import get_search_db
from app.schemas import StatusResponse
from src.auth import is_token_valid, get_token_info
from src.config import EXPORT_PROGRESS_PATH

router = APIRouter(tags=["status"])


@router.get("/status", response_model=StatusResponse)
def get_status():
    # Token info
    try:
        token_info = get_token_info()
        token_valid = is_token_valid()
        token_remaining = token_info.get("remaining_seconds", 0)
    except Exception:
        token_valid = False
        token_remaining = 0

    # DB stats
    try:
        db = get_search_db()
        db_stats = db.get_stats()
    except Exception:
        db_stats = {}

    # Export count
    export_count = 0
    try:
        if EXPORT_PROGRESS_PATH.exists():
            data = json.loads(EXPORT_PROGRESS_PATH.read_text())
            export_count = len(data.get("completed", []))
    except Exception:
        pass

    return StatusResponse(
        token_valid=token_valid,
        token_remaining_seconds=token_remaining,
        db_stats=db_stats,
        export_count=export_count,
    )
