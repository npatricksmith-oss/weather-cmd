"""NOAA Weather Alerts and Forecast API client."""

from __future__ import annotations

import re
from datetime import datetime

import httpx

from weather_cmd.models import CurrentConditions, DailyForecast, ForecastPeriod, HourlyForecast, NOAAAlert
ALERTS_URL = "https://api.weather.gov/alerts/active"
POINTS_URL = "https://api.weather.gov/points"
HEADERS = {
    "User-Agent": "(weather-cmd, github.com/weather-cmd)",
    "Accept": "application/geo+json",
}


async def fetch_alerts(lat: float, lon: float, client: httpx.AsyncClient) -> list[NOAAAlert]:
    try:
        resp = await client.get(
            ALERTS_URL,
            params={"point": f"{lat:.4f},{lon:.4f}"},
            headers=HEADERS,
            timeout=10.0,
        )
        if resp.status_code in (404, 400):
            return []
        resp.raise_for_status()
        data = resp.json()
    except (httpx.HTTPError, httpx.TimeoutException):
        return []

    alerts = []
    for feature in data.get("features", []):
        props = feature.get("properties", {})
        alerts.append(
            NOAAAlert(
                event=props.get("event", "Unknown"),
                headline=props.get("headline", ""),
                description=props.get("description", ""),
                severity=props.get("severity", "Unknown"),
                urgency=props.get("urgency", "Unknown"),
                onset=props.get("onset", ""),
                expires=props.get("expires", ""),
                sender_name=props.get("senderName", ""),
            )
        )
    return alerts


async def fetch_county(lat: float, lon: float, client: httpx.AsyncClient) -> str:
    """Fetch county name from NOAA Points API."""
    try:
        points_resp = await client.get(
            f"{POINTS_URL}/{lat:.4f},{lon:.4f}",
            headers=HEADERS,
            timeout=10.0,
        )
        if points_resp.status_code in (404, 400):
            return ""
        points_resp.raise_for_status()
        points_data = points_resp.json()

        # Extract county from properties
        county = points_data.get("properties", {}).get("county", "")
        if county:
            # County is returned as a URL, extract name from it
            # e.g., "https://api.weather.gov/zones/county/NYZ013" -> "NYZ013"
            # But we want the friendly name, which isn't in points API
            # Return just the URL for now, or parse it
            return county.split("/")[-1] if "/" in county else county

        return ""
    except (httpx.HTTPError, httpx.TimeoutException, KeyError):
        return ""


async def fetch_text_forecast(lat: float, lon: float, client: httpx.AsyncClient) -> str:
    """Fetch daily text forecast from NOAA Points API."""
    try:
        # Get grid point info which contains forecast URL
        points_resp = await client.get(
            f"{POINTS_URL}/{lat:.4f},{lon:.4f}",
            headers=HEADERS,
            timeout=10.0,
        )
        if points_resp.status_code in (404, 400):
            return ""
        points_resp.raise_for_status()
        points_data = points_resp.json()

        # Get forecast URL from properties
        forecast_url = points_data.get("properties", {}).get("forecast")
        if not forecast_url:
            return ""

        # Fetch the actual forecast
        forecast_resp = await client.get(
            forecast_url,
            headers=HEADERS,
            timeout=10.0,
        )
        forecast_resp.raise_for_status()
        forecast_data = forecast_resp.json()

        # Extract today's forecast period
        periods = forecast_data.get("properties", {}).get("periods", [])
        if periods:
            # Return the first period's text (today's forecast)
            return periods[0].get("detailedForecast", "")

        return ""
    except (httpx.HTTPError, httpx.TimeoutException, KeyError, IndexError):
        return ""


async def fetch_detailed_forecast(lat: float, lon: float, client: httpx.AsyncClient) -> list[ForecastPeriod]:
    """Fetch all detailed forecast periods from NOAA Points API."""
    try:
        # Get grid point info which contains forecast URL
        points_resp = await client.get(
            f"{POINTS_URL}/{lat:.4f},{lon:.4f}",
            headers=HEADERS,
            timeout=10.0,
        )
        if points_resp.status_code in (404, 400):
            return []
        points_resp.raise_for_status()
        points_data = points_resp.json()

        # Get forecast URL from properties
        forecast_url = points_data.get("properties", {}).get("forecast")
        if not forecast_url:
            return []

        # Fetch the actual forecast
        forecast_resp = await client.get(
            forecast_url,
            headers=HEADERS,
            timeout=10.0,
        )
        forecast_resp.raise_for_status()
        forecast_data = forecast_resp.json()

        # Extract all forecast periods
        periods = forecast_data.get("properties", {}).get("periods", [])
        detailed_forecasts = []
        for period in periods:
            detailed_forecasts.append(
                ForecastPeriod(
                    name=period.get("name", ""),
                    detailed_forecast=period.get("detailedForecast", ""),
                )
            )

        return detailed_forecasts
    except (httpx.HTTPError, httpx.TimeoutException, KeyError, IndexError):
        return []


async def fetch_forecast_fallback(
    lat: float,
    lon: float,
    client: httpx.AsyncClient,
    units: str = "imperial",
) -> tuple[CurrentConditions, HourlyForecast, DailyForecast]:
    """Fetch forecast data from NOAA when the primary provider is unavailable."""
    points_resp = await client.get(
        f"{POINTS_URL}/{lat:.4f},{lon:.4f}",
        headers=HEADERS,
        timeout=10.0,
    )
    points_resp.raise_for_status()
    points_data = points_resp.json().get("properties", {})

    hourly_url = points_data.get("forecastHourly")
    daily_url = points_data.get("forecast")
    if not hourly_url or not daily_url:
        raise ValueError("NOAA forecast URLs unavailable")

    hourly_resp = await client.get(hourly_url, headers=HEADERS, timeout=10.0)
    hourly_resp.raise_for_status()
    hourly_periods = hourly_resp.json().get("properties", {}).get("periods", [])
    if not hourly_periods:
        raise ValueError("NOAA hourly forecast unavailable")

    daily_resp = await client.get(daily_url, headers=HEADERS, timeout=10.0)
    daily_resp.raise_for_status()
    daily_periods = daily_resp.json().get("properties", {}).get("periods", [])

    current = _parse_current_from_hourly(hourly_periods[0], units)
    hourly = _parse_hourly_forecast(hourly_periods, units)
    daily = _parse_daily_forecast(daily_periods, units)
    return current, hourly, daily


def _parse_current_from_hourly(period: dict, units: str) -> CurrentConditions:
    temp = _convert_temperature(period.get("temperature", 0), period.get("temperatureUnit"), units)
    wind_speed = _convert_wind_speed(_parse_wind_speed(period.get("windSpeed", "")), units)
    return CurrentConditions(
        temperature=temp,
        apparent_temperature=temp,
        humidity=float(period.get("relativeHumidity", {}).get("value") or 0),
        wind_speed=wind_speed,
        wind_gusts=wind_speed,
        wind_direction=_wind_direction_to_degrees(period.get("windDirection", "")),
        weather_code=_short_forecast_to_wmo(period.get("shortForecast", "")),
        cloud_cover=0,
        visibility=10000,
        precipitation=0,
    )


def _parse_hourly_forecast(periods: list[dict], units: str) -> HourlyForecast:
    times = [datetime.fromisoformat(period["startTime"]) for period in periods]
    temperature = [
        _convert_temperature(period.get("temperature", 0), period.get("temperatureUnit"), units)
        for period in periods
    ]
    humidity = [float(period.get("relativeHumidity", {}).get("value") or 0) for period in periods]
    precip_prob = [float(period.get("probabilityOfPrecipitation", {}).get("value") or 0) for period in periods]
    wind_speed = [_convert_wind_speed(_parse_wind_speed(period.get("windSpeed", "")), units) for period in periods]
    weather_code = [_short_forecast_to_wmo(period.get("shortForecast", "")) for period in periods]
    wind_direction = [_wind_direction_to_degrees(period.get("windDirection", "")) for period in periods]

    return HourlyForecast(
        times=times,
        temperature=temperature,
        apparent_temperature=temperature[:],
        humidity=humidity,
        precipitation_probability=precip_prob,
        precipitation=[0.0] * len(periods),
        snowfall=[0.0] * len(periods),
        weather_code=weather_code,
        cloud_cover=[0.0] * len(periods),
        wind_speed=wind_speed,
        wind_gusts=wind_speed[:],
        visibility=[10000.0] * len(periods),
    )


def _parse_daily_forecast(periods: list[dict], units: str) -> DailyForecast:
    grouped: dict[str, dict] = {}
    for period in periods:
        day_key = period.get("startTime", "")[:10]
        if not day_key:
            continue
        entry = grouped.setdefault(
            day_key,
            {
                "date": datetime.fromisoformat(period["startTime"]),
                "weather_code": _short_forecast_to_wmo(period.get("shortForecast", "")),
                "temp_max": None,
                "temp_min": None,
                "precip_prob": 0.0,
            },
        )
        temp = _convert_temperature(period.get("temperature", 0), period.get("temperatureUnit"), units)
        entry["temp_max"] = temp if entry["temp_max"] is None else max(entry["temp_max"], temp)
        entry["temp_min"] = temp if entry["temp_min"] is None else min(entry["temp_min"], temp)
        entry["precip_prob"] = max(
            entry["precip_prob"],
            float(period.get("probabilityOfPrecipitation", {}).get("value") or 0),
        )
        if period.get("isDaytime"):
            entry["weather_code"] = _short_forecast_to_wmo(period.get("shortForecast", ""))

    ordered = sorted(grouped.values(), key=lambda item: item["date"])[:7]
    return DailyForecast(
        dates=[item["date"] for item in ordered],
        weather_code=[item["weather_code"] for item in ordered],
        temp_max=[item["temp_max"] or 0.0 for item in ordered],
        temp_min=[item["temp_min"] or 0.0 for item in ordered],
        precipitation_sum=[0.0] * len(ordered),
        snowfall_sum=[0.0] * len(ordered),
        sunrise=[],
        sunset=[],
        uv_index_max=[0.0] * len(ordered),
        precipitation_probability_max=[item["precip_prob"] for item in ordered],
    )


def _parse_wind_speed(raw: str) -> float:
    match = re.search(r"(\d+)", raw or "")
    return float(match.group(1)) if match else 0.0


def _convert_temperature(value: float, source_unit: str | None, units: str) -> float:
    temp = float(value)
    source = (source_unit or "").upper()
    if units == "metric" and source == "F":
        return (temp - 32) * 5 / 9
    if units == "imperial" and source == "C":
        return (temp * 9 / 5) + 32
    return temp


def _convert_wind_speed(value: float, units: str) -> float:
    return value if units == "imperial" else value * 1.609344


def _wind_direction_to_degrees(direction: str) -> int:
    mapping = {
        "N": 0,
        "NNE": 22,
        "NE": 45,
        "ENE": 68,
        "E": 90,
        "ESE": 112,
        "SE": 135,
        "SSE": 158,
        "S": 180,
        "SSW": 202,
        "SW": 225,
        "WSW": 248,
        "W": 270,
        "WNW": 292,
        "NW": 315,
        "NNW": 338,
    }
    return mapping.get((direction or "").upper(), 0)


def _short_forecast_to_wmo(short_forecast: str) -> int:
    text = (short_forecast or "").lower()
    if "thunder" in text:
        return 95
    if "freezing rain" in text:
        return 66
    if "snow" in text:
        return 71
    if "drizzle" in text:
        return 51
    if "rain" in text or "showers" in text:
        return 61
    if "fog" in text:
        return 45
    if "partly cloudy" in text or "partly sunny" in text:
        return 2
    if "mostly cloudy" in text or "cloudy" in text:
        return 3
    if "mostly clear" in text or "mostly sunny" in text:
        return 1
    if "clear" in text or "sunny" in text:
        return 0
    return 2
