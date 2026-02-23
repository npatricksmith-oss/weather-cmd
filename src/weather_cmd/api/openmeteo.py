"""Open-Meteo forecast API client."""

from __future__ import annotations

from datetime import datetime

import httpx

from weather_cmd.models import CurrentConditions, DailyForecast, HourlyForecast
from weather_cmd.utils.formatting import clean_nulls

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

HOURLY_VARS = [
    "temperature_2m",
    "apparent_temperature",
    "relative_humidity_2m",
    "precipitation_probability",
    "precipitation",
    "snowfall",
    "weather_code",
    "cloud_cover",
    "wind_speed_10m",
    "wind_gusts_10m",
    "visibility",
]

DAILY_VARS = [
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "snowfall_sum",
    "sunrise",
    "sunset",
    "uv_index_max",
    "weather_code",
    "precipitation_probability_max",
]

CURRENT_VARS = [
    "temperature_2m",
    "apparent_temperature",
    "relative_humidity_2m",
    "wind_speed_10m",
    "wind_gusts_10m",
    "wind_direction_10m",
    "weather_code",
    "cloud_cover",
    "visibility",
    "precipitation",
]


async def fetch_forecast(
    lat: float,
    lon: float,
    client: httpx.AsyncClient,
    units: str = "imperial",
) -> tuple[CurrentConditions, HourlyForecast, DailyForecast]:
    params: dict = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ",".join(HOURLY_VARS),
        "daily": ",".join(DAILY_VARS),
        "current": ",".join(CURRENT_VARS),
        "timezone": "auto",
        "forecast_days": 7,
    }

    if units == "imperial":
        params["temperature_unit"] = "fahrenheit"
        params["wind_speed_unit"] = "mph"
    else:
        params["temperature_unit"] = "celsius"
        params["wind_speed_unit"] = "kmh"

    # Precipitation always in mm from API; we convert at display time
    params["precipitation_unit"] = "mm"

    resp = await client.get(FORECAST_URL, params=params)
    resp.raise_for_status()
    data = resp.json()

    current = _parse_current(data["current"])
    hourly = _parse_hourly(data["hourly"])
    daily = _parse_daily(data["daily"])

    return current, hourly, daily


def _parse_current(data: dict) -> CurrentConditions:
    return CurrentConditions(
        temperature=data.get("temperature_2m", 0),
        apparent_temperature=data.get("apparent_temperature", 0),
        humidity=data.get("relative_humidity_2m", 0),
        wind_speed=data.get("wind_speed_10m", 0),
        wind_gusts=data.get("wind_gusts_10m", 0),
        wind_direction=data.get("wind_direction_10m", 0),
        weather_code=data.get("weather_code", 0),
        cloud_cover=data.get("cloud_cover", 0),
        visibility=data.get("visibility", 10000),
        precipitation=data.get("precipitation", 0),
    )


def _parse_hourly(data: dict) -> HourlyForecast:
    times = [datetime.fromisoformat(t) for t in data["time"]]
    return HourlyForecast(
        times=times,
        temperature=clean_nulls(data.get("temperature_2m", [])),
        apparent_temperature=clean_nulls(data.get("apparent_temperature", [])),
        humidity=clean_nulls(data.get("relative_humidity_2m", [])),
        precipitation_probability=clean_nulls(data.get("precipitation_probability", [])),
        precipitation=clean_nulls(data.get("precipitation", [])),
        snowfall=clean_nulls(data.get("snowfall", [])),
        weather_code=[c or 0 for c in data.get("weather_code", [])],
        cloud_cover=clean_nulls(data.get("cloud_cover", [])),
        wind_speed=clean_nulls(data.get("wind_speed_10m", [])),
        wind_gusts=clean_nulls(data.get("wind_gusts_10m", [])),
        visibility=clean_nulls(data.get("visibility", []), default=10000),
    )


def _parse_daily(data: dict) -> DailyForecast:
    dates = [datetime.fromisoformat(t) for t in data["time"]]
    return DailyForecast(
        dates=dates,
        weather_code=[c or 0 for c in data.get("weather_code", [])],
        temp_max=clean_nulls(data.get("temperature_2m_max", [])),
        temp_min=clean_nulls(data.get("temperature_2m_min", [])),
        precipitation_sum=clean_nulls(data.get("precipitation_sum", [])),
        snowfall_sum=clean_nulls(data.get("snowfall_sum", [])),
        sunrise=data.get("sunrise", []),
        sunset=data.get("sunset", []),
        uv_index_max=clean_nulls(data.get("uv_index_max", [])),
        precipitation_probability_max=clean_nulls(data.get("precipitation_probability_max", [])),
    )
