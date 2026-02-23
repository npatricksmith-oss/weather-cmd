"""NOAA Weather Alerts and Forecast API client."""

from __future__ import annotations

import httpx

from weather_cmd.models import NOAAAlert

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
