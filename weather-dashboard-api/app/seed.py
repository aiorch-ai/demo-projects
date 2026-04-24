"""Idempotent demo data seeder for the Weather Dashboard API."""
from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timedelta


# Fixed city UUIDs so repeat runs stay idempotent.
_CITY_LONDON = "c1a0b1c4-0001-4a1a-8a1a-000000000001"
_CITY_TOKYO = "c1a0b1c4-0002-4a1a-8a1a-000000000002"
_CITY_NEW_YORK = "c1a0b1c4-0003-4a1a-8a1a-000000000003"
_CITY_SYDNEY = "c1a0b1c4-0004-4a1a-8a1a-000000000004"
_CITY_BERLIN = "c1a0b1c4-0005-4a1a-8a1a-000000000005"

_CITIES: list[tuple[str, str, str, float, float, int]] = [
    (_CITY_LONDON, "London", "UK", 51.5074, -0.1278, 0),
    (_CITY_TOKYO, "Tokyo", "JP", 35.6762, 139.6503, 1),
    (_CITY_NEW_YORK, "New York", "US", 40.7128, -74.0060, 0),
    (_CITY_SYDNEY, "Sydney", "AU", -33.8688, 151.2093, 1),
    (_CITY_BERLIN, "Berlin", "DE", 52.5200, 13.4050, 0),
]

_CONDITIONS = ["sunny", "cloudy", "rainy", "partly_cloudy", "stormy", "snowy"]

# Realistic weather readings per city: (temperature_c, humidity, wind_speed_kmh, condition)
_WEATHER_DATA: dict[str, list[tuple[float, int, float, str]]] = {
    "London": [
        (12.5, 72, 18.5, "rainy"),
        (14.0, 68, 15.0, "cloudy"),
        (11.0, 80, 22.0, "stormy"),
        (15.5, 65, 12.0, "partly_cloudy"),
        (9.0, 85, 20.0, "rainy"),
        (8.5, 78, 16.0, "cloudy"),
    ],
    "Tokyo": [
        (22.0, 60, 10.0, "sunny"),
        (24.5, 55, 8.0, "sunny"),
        (20.0, 70, 14.0, "cloudy"),
        (18.5, 75, 12.0, "rainy"),
        (26.0, 50, 6.0, "sunny"),
        (21.0, 65, 11.0, "partly_cloudy"),
    ],
    "New York": [
        (10.0, 55, 20.0, "sunny"),
        (8.5, 60, 18.0, "partly_cloudy"),
        (5.0, 65, 25.0, "cloudy"),
        (2.0, 70, 22.0, "snowy"),
        (12.0, 50, 15.0, "sunny"),
        (7.0, 62, 19.0, "rainy"),
    ],
    "Sydney": [
        (25.0, 55, 14.0, "sunny"),
        (23.5, 60, 16.0, "partly_cloudy"),
        (27.0, 50, 12.0, "sunny"),
        (22.0, 65, 18.0, "cloudy"),
        (20.5, 70, 20.0, "rainy"),
        (26.0, 52, 10.0, "sunny"),
    ],
    "Berlin": [
        (11.0, 68, 14.0, "cloudy"),
        (13.5, 62, 12.0, "partly_cloudy"),
        (9.0, 75, 18.0, "rainy"),
        (6.0, 80, 20.0, "snowy"),
        (15.0, 55, 10.0, "sunny"),
        (10.5, 70, 16.0, "cloudy"),
    ],
}


def seed_demo_data(db_path: str) -> None:
    """Populate the database with demo cities and weather records.

    Idempotent via INSERT OR IGNORE on cities (UNIQUE(name, country)) and
    existence checks for weather records.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        # Insert cities with INSERT OR IGNORE
        conn.executemany(
            """
            INSERT OR IGNORE INTO cities
            (id, name, country, latitude, longitude, is_favourite)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            _CITIES,
        )

        # Build a mapping from city name to city_id for weather records
        city_id_map: dict[str, str] = {}
        for city_id, name, *_ in _CITIES:
            city_id_map[name] = city_id

        # Insert weather records if they don't already exist for this city+recorded_at
        base_time = datetime(2024, 1, 15, 8, 0, 0)
        for city_name, records in _WEATHER_DATA.items():
            city_id = city_id_map[city_name]
            for idx, (temp, humidity, wind, condition) in enumerate(records):
                recorded_at = (base_time + timedelta(hours=idx * 4)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                existing = conn.execute(
                    "SELECT 1 FROM weather_records WHERE city_id = ? AND recorded_at = ?",
                    (city_id, recorded_at),
                ).fetchone()
                if existing is not None:
                    continue
                record_id = uuid.uuid4().hex
                conn.execute(
                    """
                    INSERT INTO weather_records
                    (id, city_id, temperature_c, humidity, wind_speed_kmh, condition, recorded_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (record_id, city_id, temp, humidity, wind, condition, recorded_at),
                )

        conn.commit()
    finally:
        conn.close()
