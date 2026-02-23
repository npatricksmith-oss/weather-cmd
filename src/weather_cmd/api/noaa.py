"""NOAA Weather Alerts and Forecast API client."""

from __future__ import annotations

import httpx

from weather_cmd.models import ForecastPeriod, NOAAAlert

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
