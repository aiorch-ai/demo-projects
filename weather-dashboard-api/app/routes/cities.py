"""Cities router: CRUD, favourite toggle, and weather summary."""
from __future__ import annotations

import sqlite3
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.database import get_db
from app.models import CityCreate, CityResponse, CityWeatherSummary, WeatherRecordResponse


router = APIRouter(prefix="/api/cities", tags=["cities"])


def _row_to_city_response(row: sqlite3.Row) -> CityResponse:
    return CityResponse(
        id=row["id"],
        name=row["name"],
        country=row["country"],
        latitude=row["latitude"],
        longitude=row["longitude"],
        is_favourite=bool(row["is_favourite"]),
        created_at=row["created_at"],
    )


@router.post("", response_model=CityResponse, status_code=status.HTTP_201_CREATED)
def create_city(payload: CityCreate) -> CityResponse:
    city_id = uuid.uuid4().hex
    with get_db() as db:
        try:
            db.execute(
                """
                INSERT INTO cities (id, name, country, latitude, longitude, is_favourite)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (city_id, payload.name, payload.country, payload.latitude, payload.longitude, 0),
            )
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="city with this name and country already exists",
            )
        row = db.execute("SELECT * FROM cities WHERE id = ?", (city_id,)).fetchone()
    return _row_to_city_response(row)


@router.get("", response_model=list[CityResponse])
def list_cities(
    country: str | None = None,
    is_favourite: bool | None = None,
) -> list[CityResponse]:
    where: list[str] = []
    params: list[Any] = []

    if country is not None:
        where.append("country = ?")
        params.append(country)
    if is_favourite is not None:
        where.append("is_favourite = ?")
        params.append(1 if is_favourite else 0)

    sql = "SELECT * FROM cities"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY created_at DESC, id"

    with get_db() as db:
        rows = db.execute(sql, params).fetchall()
    return [_row_to_city_response(r) for r in rows]


@router.get("/{city_id}", response_model=CityResponse)
def get_city(city_id: str) -> CityResponse:
    with get_db() as db:
        row = db.execute("SELECT * FROM cities WHERE id = ?", (city_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="city not found")
    return _row_to_city_response(row)


@router.delete("/{city_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_city(city_id: str) -> None:
    with get_db() as db:
        cursor = db.execute("DELETE FROM cities WHERE id = ?", (city_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="city not found")


@router.post("/{city_id}/favourite", response_model=CityResponse)
def toggle_favourite(city_id: str) -> CityResponse:
    with get_db() as db:
        row = db.execute("SELECT * FROM cities WHERE id = ?", (city_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="city not found")
        new_value = 0 if row["is_favourite"] else 1
        db.execute(
            "UPDATE cities SET is_favourite = ? WHERE id = ?",
            (new_value, city_id),
        )
        row = db.execute("SELECT * FROM cities WHERE id = ?", (city_id,)).fetchone()
    return _row_to_city_response(row)


@router.get("/{city_id}/summary", response_model=CityWeatherSummary)
def city_summary(city_id: str) -> CityWeatherSummary:
    with get_db() as db:
        city_row = db.execute("SELECT * FROM cities WHERE id = ?", (city_id,)).fetchone()
        if city_row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="city not found")

        latest_row = db.execute(
            """
            SELECT * FROM weather_records
            WHERE city_id = ?
            ORDER BY recorded_at DESC
            LIMIT 1
            """,
            (city_id,),
        ).fetchone()

        count_row = db.execute(
            "SELECT COUNT(*) AS c FROM weather_records WHERE city_id = ?",
            (city_id,),
        ).fetchone()

    city = _row_to_city_response(city_row)
    latest: WeatherRecordResponse | None = None
    if latest_row is not None:
        latest = WeatherRecordResponse(
            id=latest_row["id"],
            city_id=latest_row["city_id"],
            temperature_c=latest_row["temperature_c"],
            humidity=latest_row["humidity"],
            wind_speed_kmh=latest_row["wind_speed_kmh"],
            condition=latest_row["condition"],
            recorded_at=latest_row["recorded_at"],
        )

    return CityWeatherSummary(city=city, latest=latest, record_count=count_row["c"])
