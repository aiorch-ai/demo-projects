"""Seed demo data for the bookmark manager database."""

import sqlite3


def seed_demo_data(db_path: str) -> None:
    """Insert deterministic demo data into the database at db_path.

    Uses INSERT OR IGNORE for idempotency — safe to call multiple times.
    """
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")

        # ---------- collections ----------
        collections = [
            ("col-development", "Development", None, "#3b82f6"),
            ("col-design", "Design", None, "#f59e0b"),
            ("col-research", "Research", None, "#8b5cf6"),
        ]
        conn.executemany(
            "INSERT OR IGNORE INTO collections (id, name, description, color) VALUES (?, ?, ?, ?)",
            collections,
        )

        # ---------- tags ----------
        tags = [
            ("python",),
            ("javascript",),
            ("api",),
            ("design",),
            ("ai",),
            ("database",),
            ("frontend",),
            ("backend",),
            ("devops",),
            ("security",),
        ]
        conn.executemany(
            "INSERT OR IGNORE INTO tags (name) VALUES (?)",
            tags,
        )

        # ---------- bookmarks ----------
        # 5 in Development, 4 in Design, 3 in Research, 3 with NULL collection_id
        # exactly 4 marked is_favourite=1
        bookmarks = [
            # Development (col-development) — 5 bookmarks
            ("bm-001", "https://github.com/", "GitHub", "Code hosting and collaboration platform", "col-development", 1),
            ("bm-002", "https://developer.mozilla.org/", "MDN Web Docs", "Documentation for web developers", "col-development", 0),
            ("bm-003", "https://stackoverflow.com/", "Stack Overflow", "Q&A for professional programmers", "col-development", 1),
            ("bm-004", "https://docs.python.org/", "Python Documentation", "Official Python language documentation", "col-development", 0),
            ("bm-005", "https://fastapi.tiangolo.com/", "FastAPI", "Modern web framework for building APIs", "col-development", 0),
            # Design (col-design) — 4 bookmarks
            ("bm-006", "https://dribbble.com/", "Dribbble", "Design inspiration and portfolio platform", "col-design", 1),
            ("bm-007", "https://www.figma.com/", "Figma", "Collaborative interface design tool", "col-design", 0),
            ("bm-008", "https://colorhunt.co/", "Color Hunt", "Color palettes for designers and developers", "col-design", 0),
            ("bm-009", "https://fonts.google.com/", "Google Fonts", "Library of free licensed font families", "col-design", 1),
            # Research (col-research) — 3 bookmarks
            ("bm-010", "https://arxiv.org/", "arXiv", "Open-access scientific papers repository", "col-research", 0),
            ("bm-011", "https://scholar.google.com/", "Google Scholar", "Search for academic literature", "col-research", 0),
            ("bm-012", "https://www.nature.com/", "Nature", "Leading international science journal", "col-research", 0),
            # No collection — 3 bookmarks
            ("bm-013", "https://news.ycombinator.com/", "Hacker News", "Technology and startup news aggregator", None, 0),
            ("bm-014", "https://www.reddit.com/r/programming/", "r/programming", "Programming community on Reddit", None, 0),
            ("bm-015", "https://medium.com/", "Medium", "Publishing platform for articles and ideas", None, 0),
        ]
        conn.executemany(
            "INSERT OR IGNORE INTO bookmarks (id, url, title, description, collection_id, is_favourite) VALUES (?, ?, ?, ?, ?, ?)",
            bookmarks,
        )

        # ---------- bookmark_tags ----------
        bookmark_tags = [
            # bm-001: GitHub -> python, backend, devops
            ("bm-001", "python"),
            ("bm-001", "backend"),
            ("bm-001", "devops"),
            # bm-002: MDN -> javascript, frontend
            ("bm-002", "javascript"),
            ("bm-002", "frontend"),
            # bm-003: Stack Overflow -> python, javascript, backend
            ("bm-003", "python"),
            ("bm-003", "javascript"),
            ("bm-003", "backend"),
            # bm-004: Python Docs -> python
            ("bm-004", "python"),
            # bm-005: FastAPI -> python, api, backend
            ("bm-005", "python"),
            ("bm-005", "api"),
            ("bm-005", "backend"),
            # bm-006: Dribbble -> design, frontend
            ("bm-006", "design"),
            ("bm-006", "frontend"),
            # bm-007: Figma -> design, frontend
            ("bm-007", "design"),
            ("bm-007", "frontend"),
            # bm-008: Color Hunt -> design
            ("bm-008", "design"),
            # bm-009: Google Fonts -> design, frontend
            ("bm-009", "design"),
            ("bm-009", "frontend"),
            # bm-010: arXiv -> ai
            ("bm-010", "ai"),
            # bm-011: Google Scholar -> ai
            ("bm-011", "ai"),
            # bm-012: Nature -> ai, security
            ("bm-012", "ai"),
            ("bm-012", "security"),
            # bm-013: Hacker News -> devops, security
            ("bm-013", "devops"),
            ("bm-013", "security"),
            # bm-014: r/programming -> python, javascript, frontend
            ("bm-014", "python"),
            ("bm-014", "javascript"),
            ("bm-014", "frontend"),
            # bm-015: Medium -> database, api
            ("bm-015", "database"),
            ("bm-015", "api"),
        ]
        conn.executemany(
            "INSERT OR IGNORE INTO bookmark_tags (bookmark_id, tag_name) VALUES (?, ?)",
            bookmark_tags,
        )

        conn.commit()
    finally:
        conn.close()
