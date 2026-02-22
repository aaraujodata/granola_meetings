"""Search router: full-text search across meeting content."""

from fastapi import APIRouter, Query

from app.dependencies import get_search_db
from app.schemas import SearchResult

router = APIRouter(tags=["search"])


@router.get("/search", response_model=list[SearchResult])
def search_meetings(
    q: str = Query(..., min_length=1),
    type: str | None = Query(None, alias="type"),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    db = get_search_db()
    results = db.search(
        query=q,
        content_type=type,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )
    return [SearchResult(**r) for r in results]
