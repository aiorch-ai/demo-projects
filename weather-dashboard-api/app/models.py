"""Pydantic v2 models for the Weather Dashboard API."""
from __future__ import annotations

from pydantic import BaseModel


class CityCreate(BaseModel):
    name: str
    country: str
    latitude: float
    longitude: float


class CityResponse(BaseModel):
    id: str
    name: str
    country: str
    latitude: float
    longitude: float
    is_favourite: bool
    created_at: str


class WeatherRecordCreate(BaseModel):
    city_id: str
    temperature_c: float
    humidity: int
    wind_speed_kmh: float
    condition: str
    recorded_at: str | None = None


class WeatherRecordResponse(BaseModel):
    id: str
    city_id: str
    temperature_c: float
    humidity: int
    wind_speed_kmh: float
    condition: str
    recorded_at: str


class CityWeatherSummary(BaseModel):
    city: CityResponse
    latest: WeatherRecordResponse | None
    record_count: int
