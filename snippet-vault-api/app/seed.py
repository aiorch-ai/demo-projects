"""Idempotent demo data seeder for the Snippet Vault API."""
from __future__ import annotations

import sqlite3


_TAGS = [
    ("advanced",),
    ("algorithm",),
    ("api",),
    ("beginner",),
    ("database",),
    ("devops",),
    ("utility",),
    ("web",),
]

_SNIPPETS: list[dict[str, object]] = [
    {
        "id": "61ef6f34-4f0d-4bc0-8c89-c1d7e6c9d101",
        "title": "Fibonacci with memoization",
        "code": """def fibonacci(n: int, cache: dict[int, int] | None = None) -> int:\n    if cache is None:\n        cache = {0: 0, 1: 1}\n    if n not in cache:\n        cache[n] = fibonacci(n - 1, cache) + fibonacci(n - 2, cache)\n    return cache[n]\n""",
        "language": "python",
        "description": "Recursive fibonacci implementation that avoids repeated work.",
        "is_public": 1,
        "view_count": 18,
        "created_at": "2024-02-01 09:00:00",
        "updated_at": "2024-02-01 09:00:00",
        "tags": ["algorithm", "beginner"],
    },
    {
        "id": "84e0c762-1b35-4ea0-b8c4-0762cb6d6d02",
        "title": "FastAPI pagination helper",
        "code": """from collections.abc import Sequence\n\n\ndef paginate(items: Sequence[dict], limit: int, offset: int) -> dict:\n    return {\n        \"items\": list(items[offset : offset + limit]),\n        \"limit\": limit,\n        \"offset\": offset,\n        \"total\": len(items),\n    }\n""",
        "language": "python",
        "description": "Small utility to package list responses with offset metadata.",
        "is_public": 1,
        "view_count": 11,
        "created_at": "2024-02-02 10:30:00",
        "updated_at": "2024-02-04 08:15:00",
        "tags": ["api", "utility"],
    },
    {
        "id": "f3adb7e0-7c6e-4dc2-a585-1ce9ec5af603",
        "title": "Fetch JSON with timeout",
        "code": """export async function fetchJson(url, options = {}) {\n  const controller = new AbortController();\n  const timeout = setTimeout(() => controller.abort(), options.timeout ?? 5000);\n\n  try {\n    const response = await fetch(url, { ...options, signal: controller.signal });\n    if (!response.ok) {\n      throw new Error(`Request failed: ${response.status}`);\n    }\n    return await response.json();\n  } finally {\n    clearTimeout(timeout);\n  }\n}\n""",
        "language": "javascript",
        "description": "Wrap fetch with timeout handling and JSON decoding.",
        "is_public": 1,
        "view_count": 27,
        "created_at": "2024-02-03 13:00:00",
        "updated_at": "2024-02-03 13:00:00",
        "tags": ["web", "api", "utility"],
    },
    {
        "id": "8f6db5df-2f39-45d4-8d36-08b06595d904",
        "title": "Debounced search input",
        "code": """export function debounce(fn, wait = 250) {\n  let timer;\n  return (...args) => {\n    clearTimeout(timer);\n    timer = setTimeout(() => fn(...args), wait);\n  };\n}\n""",
        "language": "javascript",
        "description": "Client-side debounce helper for search boxes and autosave flows.",
        "is_public": 0,
        "view_count": 6,
        "created_at": "2024-02-04 09:20:00",
        "updated_at": "2024-02-05 07:45:00",
        "tags": ["web", "beginner"],
    },
    {
        "id": "2d917cd3-7a60-4b56-9367-52a88bca2b05",
        "title": "HTTP JSON health handler",
        "code": """package main\n\nimport (\n    \"encoding/json\"\n    \"net/http\"\n)\n\nfunc healthHandler(w http.ResponseWriter, r *http.Request) {\n    w.Header().Set(\"Content-Type\", \"application/json\")\n    _ = json.NewEncoder(w).Encode(map[string]string{\"status\": \"ok\"})\n}\n""",
        "language": "go",
        "description": "Minimal HTTP handler for a JSON health endpoint.",
        "is_public": 1,
        "view_count": 14,
        "created_at": "2024-02-05 08:00:00",
        "updated_at": "2024-02-05 08:00:00",
        "tags": ["web", "api"],
    },
    {
        "id": "b65abf03-afda-4f8c-b4a5-4a7068352b06",
        "title": "Worker pool with channels",
        "code": """package main\n\nimport \"sync\"\n\nfunc runWorkers(jobs []string, workerCount int, fn func(string)) {\n    ch := make(chan string)\n    var wg sync.WaitGroup\n\n    for i := 0; i < workerCount; i++ {\n        wg.Add(1)\n        go func() {\n            defer wg.Done()\n            for job := range ch {\n                fn(job)\n            }\n        }()\n    }\n\n    for _, job := range jobs {\n        ch <- job\n    }\n    close(ch)\n    wg.Wait()\n}\n""",
        "language": "go",
        "description": "Basic worker pool pattern for bounded concurrency.",
        "is_public": 0,
        "view_count": 21,
        "created_at": "2024-02-06 11:10:00",
        "updated_at": "2024-02-07 10:00:00",
        "tags": ["advanced", "utility"],
    },
    {
        "id": "4bd590b6-1bba-491f-b13a-bc7a73c94907",
        "title": "Top orders per customer",
        "code": """WITH ranked_orders AS (\n    SELECT\n        customer_id,\n        order_id,\n        total_amount,\n        ROW_NUMBER() OVER (\n            PARTITION BY customer_id\n            ORDER BY total_amount DESC\n        ) AS rank_in_customer\n    FROM orders\n)\nSELECT customer_id, order_id, total_amount\nFROM ranked_orders\nWHERE rank_in_customer <= 3;\n""",
        "language": "sql",
        "description": "Window function example for ranking each customer's highest orders.",
        "is_public": 1,
        "view_count": 33,
        "created_at": "2024-02-07 14:30:00",
        "updated_at": "2024-02-07 14:30:00",
        "tags": ["database", "advanced"],
    },
    {
        "id": "c03415d2-d4bb-4f35-a4eb-4ca8d5fbe808",
        "title": "Safe upsert for tag counts",
        "code": """INSERT INTO tag_usage (tag_name, usage_count)\nVALUES (?, 1)\nON CONFLICT(tag_name)\nDO UPDATE SET usage_count = tag_usage.usage_count + 1;\n""",
        "language": "sql",
        "description": "Increment a tag usage counter with a single statement.",
        "is_public": 0,
        "view_count": 9,
        "created_at": "2024-02-08 15:00:00",
        "updated_at": "2024-02-08 15:00:00",
        "tags": ["database", "api"],
    },
    {
        "id": "9a8f4b77-9d5f-4d3b-b15c-557b2c4dcb09",
        "title": "Rotate logs older than seven days",
        "code": """#!/usr/bin/env bash\nset -euo pipefail\n\nlog_dir=${1:-/var/log/myapp}\narchive_dir=\"$log_dir/archive\"\nmkdir -p \"$archive_dir\"\n\nfind \"$log_dir\" -maxdepth 1 -type f -name '*.log' -mtime +7 -print0 |\nwhile IFS= read -r -d '' file; do\n  gzip -c \"$file\" > \"$archive_dir/$(basename \"$file\").gz\"\n  : > \"$file\"\ndone\n""",
        "language": "bash",
        "description": "Archive and truncate logs that have aged past a retention window.",
        "is_public": 1,
        "view_count": 17,
        "created_at": "2024-02-09 06:50:00",
        "updated_at": "2024-02-09 06:50:00",
        "tags": ["devops", "utility"],
    },
    {
        "id": "cb8d0cd4-8cb0-4cb8-8b7f-9d26c2105810",
        "title": "Wait for service readiness",
        "code": """#!/usr/bin/env bash\nset -euo pipefail\n\nhost=${1:?host required}\nport=${2:?port required}\nretries=${3:-20}\n\nfor ((i=1; i<=retries; i++)); do\n  if nc -z \"$host\" \"$port\"; then\n    echo \"service is ready\"\n    exit 0\n  fi\n  sleep 1\ndone\n\necho \"service did not become ready\" >&2\nexit 1\n""",
        "language": "bash",
        "description": "Retry loop used in CI and container startup scripts.",
        "is_public": 1,
        "view_count": 24,
        "created_at": "2024-02-10 07:10:00",
        "updated_at": "2024-02-11 05:40:00",
        "tags": ["devops", "beginner"],
    },
]


def seed_demo_data(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        conn.executemany("INSERT OR IGNORE INTO tags (name) VALUES (?)", _TAGS)

        conn.executemany(
            """
            INSERT OR IGNORE INTO snippets (
                id,
                title,
                code,
                language,
                description,
                is_public,
                view_count,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    snippet["id"],
                    snippet["title"],
                    snippet["code"],
                    snippet["language"],
                    snippet["description"],
                    snippet["is_public"],
                    snippet["view_count"],
                    snippet["created_at"],
                    snippet["updated_at"],
                )
                for snippet in _SNIPPETS
            ],
        )

        conn.executemany(
            """
            INSERT OR IGNORE INTO snippet_tags (snippet_id, tag_name)
            VALUES (?, ?)
            """,
            [
                (str(snippet["id"]), tag_name)
                for snippet in _SNIPPETS
                for tag_name in snippet["tags"]
            ],
        )

        conn.commit()
    finally:
        conn.close()
