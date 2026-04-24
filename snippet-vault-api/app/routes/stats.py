"""Statistics routes for languages and popular snippets."""
from __future__ import annotations

from fastapi import APIRouter

from app.database import get_db
from app.models import LanguageStats, SnippetResponse
from app.routes.snippets import _fetch_tags, _row_to_snippet_response


router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/languages", response_model=list[LanguageStats])
def language_stats() -> list[LanguageStats]:
    with get_db() as db:
        rows = db.execute(
            """
            SELECT language, COUNT(*) AS snippet_count
            FROM snippets
            GROUP BY language
            ORDER BY snippet_count DESC, language ASC
            """
        ).fetchall()
    return [
        LanguageStats(language=row["language"], snippet_count=row["snippet_count"])
        for row in rows
    ]


@router.get("/popular", response_model=list[SnippetResponse])
def popular_snippets() -> list[SnippetResponse]:
    with get_db() as db:
        rows = db.execute(
            """
            SELECT *
            FROM snippets
            ORDER BY view_count DESC, created_at DESC, id ASC
            LIMIT 5
            """
        ).fetchall()
        snippet_ids = [row["id"] for row in rows]
        tag_map = _fetch_tags(db, snippet_ids)
    return [_row_to_snippet_response(row, tag_map) for row in rows]
