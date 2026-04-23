"""Idempotent demo data seeder for the Bookmark Manager API."""
from __future__ import annotations

import sqlite3
import uuid


# Fixed collection UUIDs so repeat runs stay idempotent.
_COLLECTION_DEVELOPMENT = "a1f0c2d4-0001-4a1a-8a1a-000000000001"
_COLLECTION_DESIGN = "a1f0c2d4-0002-4a1a-8a1a-000000000002"
_COLLECTION_RESEARCH = "a1f0c2d4-0003-4a1a-8a1a-000000000003"


_COLLECTIONS: list[tuple[str, str, str | None, str]] = [
    (_COLLECTION_DEVELOPMENT, "Development", "Code, docs, and developer tools", "#3b82f6"),
    (_COLLECTION_DESIGN, "Design", "UI/UX inspiration and design resources", "#f59e0b"),
    (_COLLECTION_RESEARCH, "Research", "Papers, articles, and academic references", "#8b5cf6"),
]


# Tag vocabulary (9 tags from the allowed set).
_TAGS: list[str] = [
    "python",
    "javascript",
    "api",
    "design",
    "ai",
    "database",
    "frontend",
    "backend",
    "devops",
]


# Bookmarks: (url, title, description, collection_id, is_favourite, tags)
_BOOKMARKS: list[tuple[str, str, str, str | None, int, list[str]]] = [
    # Development (5)
    (
        "https://github.com",
        "GitHub",
        "Where the world builds software. Host Git repos and collaborate on code.",
        _COLLECTION_DEVELOPMENT,
        1,
        ["devops", "backend"],
    ),
    (
        "https://stackoverflow.com",
        "Stack Overflow",
        "Q&A site for professional and enthusiast programmers.",
        _COLLECTION_DEVELOPMENT,
        0,
        ["python", "javascript", "backend"],
    ),
    (
        "https://developer.mozilla.org",
        "MDN Web Docs",
        "Resources for developers, by developers: HTML, CSS, and JavaScript references.",
        _COLLECTION_DEVELOPMENT,
        1,
        ["javascript", "frontend"],
    ),
    (
        "https://docs.python.org",
        "Python Documentation",
        "Official Python language and standard library documentation.",
        _COLLECTION_DEVELOPMENT,
        0,
        ["python"],
    ),
    (
        "https://fastapi.tiangolo.com",
        "FastAPI",
        "Modern, fast (high-performance) web framework for building APIs with Python.",
        _COLLECTION_DEVELOPMENT,
        1,
        ["python", "api", "backend"],
    ),
    # Design (4)
    (
        "https://dribbble.com",
        "Dribbble",
        "Discover the world's top designers and creative professionals.",
        _COLLECTION_DESIGN,
        0,
        ["design", "frontend"],
    ),
    (
        "https://www.behance.net",
        "Behance",
        "Showcase and discover creative work from designers worldwide.",
        _COLLECTION_DESIGN,
        0,
        ["design"],
    ),
    (
        "https://www.figma.com",
        "Figma",
        "Collaborative interface design tool used by product teams.",
        _COLLECTION_DESIGN,
        1,
        ["design", "frontend"],
    ),
    (
        "https://www.refactoringui.com",
        "Refactoring UI",
        "Practical tips for designing better interfaces, from the creators of Tailwind CSS.",
        _COLLECTION_DESIGN,
        0,
        ["design"],
    ),
    # Research (3)
    (
        "https://arxiv.org",
        "arXiv",
        "Open-access archive for scholarly articles in physics, math, CS, and more.",
        _COLLECTION_RESEARCH,
        0,
        ["ai"],
    ),
    (
        "https://paperswithcode.com",
        "Papers with Code",
        "Free and open resource with machine learning papers, code, and evaluation tables.",
        _COLLECTION_RESEARCH,
        0,
        ["ai", "database"],
    ),
    (
        "https://scholar.google.com",
        "Google Scholar",
        "Search broadly for scholarly literature across disciplines and sources.",
        _COLLECTION_RESEARCH,
        0,
        ["ai"],
    ),
    # No collection (3)
    (
        "https://news.ycombinator.com",
        "Hacker News",
        "Social news site focusing on computer science and entrepreneurship.",
        None,
        0,
        ["backend", "devops"],
    ),
    (
        "https://www.wikipedia.org",
        "Wikipedia",
        "The free encyclopedia that anyone can edit.",
        None,
        0,
        ["api"],
    ),
    (
        "https://www.reddit.com",
        "Reddit",
        "The front page of the internet: communities for every topic imaginable.",
        None,
        0,
        ["javascript"],
    ),
]


def seed_demo_data(db_path: str) -> None:
    """Populate the database with demo collections, tags, and bookmarks.

    Idempotent:
      - collections use INSERT OR IGNORE on the UNIQUE(name) column.
      - tags use INSERT OR IGNORE on the PK(name) column.
      - bookmarks are gated by a SELECT existence check on url, since the
        schema does not declare UNIQUE(url).
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        # Collections
        conn.executemany(
            "INSERT OR IGNORE INTO collections (id, name, description, color) VALUES (?, ?, ?, ?)",
            _COLLECTIONS,
        )

        # Tags
        conn.executemany(
            "INSERT OR IGNORE INTO tags (name) VALUES (?)",
            [(t,) for t in _TAGS],
        )

        # Bookmarks — gate by url existence.
        for url, title, description, collection_id, is_favourite, tags in _BOOKMARKS:
            existing = conn.execute(
                "SELECT 1 FROM bookmarks WHERE url = ?", (url,)
            ).fetchone()
            if existing is not None:
                continue
            bookmark_id = uuid.uuid4().hex
            conn.execute(
                """
                INSERT INTO bookmarks (id, url, title, description, collection_id, is_favourite)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (bookmark_id, url, title, description, collection_id, is_favourite),
            )
            for tag_name in tags:
                conn.execute(
                    "INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,)
                )
                conn.execute(
                    "INSERT OR IGNORE INTO bookmark_tags (bookmark_id, tag_name) VALUES (?, ?)",
                    (bookmark_id, tag_name),
                )

        conn.commit()
    finally:
        conn.close()
