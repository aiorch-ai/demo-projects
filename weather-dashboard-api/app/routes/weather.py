"""Weather records router: create, list, latest, delete."""
from __future__ import annotations

import sqlite3
import uuid

from fastapi import APIRouter, HTTPException, status

from app.database import get_db
from app.models import WeatherRecordCreate, WeatherRecordResponse


router = APIRouter(prefix="/api/weather", tags=["weather"])


def _row_to_response(row: sqlite3.Row) -> WeatherRecordResponse:
    return WeatherRecordResponse(
        id=row["id"],
        city_id=row["city_id"],
        temperature_c=row["temperature_c"],
        humidity=row["humidity"],
        wind_speed_kmh=row["wind_speed_kmh"],
        condition=row["condition"],
        recorded_at=row["recorded_at"],
    )


@router.post("", response_model=WeatherRecordResponse, status_code=status.HTTP_201_CREATED)
def record_weather(payload: WeatherRecordCreate) -> WeatherRecordResponse:
    record_id = uuid.uuid4().hex
    with get_db() as db:
        city = db.execute("SELECT 1 FROM cities WHERE id = ?", (payload.city_id,)).fetchone()
        if city is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="city not found",
            )
        db.execute(
            """
            INSERT INTO weather_records
            (id, city_id, temperature_c, humidity, wind_speed_kmh, condition, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?, COALESCE(?, datetime('now')))
            """,
            (
                record_id,
                payload.city_id,
                payload.temperature_c,
                payload.humidity,
                payload.wind_speed_kmh,
                payload.condition,
                payload.recorded_at,
            ),
        )
        row = db.execute("SELECT * FROM weather_records WHERE id = ?", (record_id,)).fetchone()
    return _row_to_response(row)


@router.get("/{city_id}", response_model=list[WeatherRecordResponse])
def weather_history(
    city_id: str,
    limit: int = 50,
    offset: int = 0,
) -> list[WeatherRecordResponse]:
    with get_db() as db:
        rows = db.execute(
            """
            SELECT * FROM weather_records
            WHERE city_id = ?
            ORDER BY recorded_at DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            (city_id, limit, offset),
        ).fetchall()
    return [_row_to_response(r) for r in rows]


@router.get("/{city_id}/latest", response_model=WeatherRecordResponse)
def weather_latest(city_id: str) -> WeatherRecordResponse:
    with get_db() as db:
        row = db.execute(
            """
            SELECT * FROM weather_records
            WHERE city_id = ?
            ORDER BY recorded_at DESC, id DESC
            LIMIT 1
            """,
            (city_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no weather records found for this city",
        )
    return _row_to_response(row)


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_weather_record(record_id: str) -> None:
    with get_db() as db:
        cursor = db.execute("DELETE FROM weather_records WHERE id = ?", (record_id,))
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="weather record not found",
            )
