"""NOAA Weather Alerts API client."""

from __future__ import annotations

import httpx

from weather_cmd.models import NOAAAlert

ALERTS_URL = "https://api.weather.gov/alerts/active"
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
