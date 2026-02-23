"""Location resolution: city name, coordinates, or IP fallback."""

from __future__ import annotations

import httpx

from weather_cmd.models import Location

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
IP_URL = "https://ipapi.co/json/"


async def geocode_city(city: str, client: httpx.AsyncClient) -> Location:
    resp = await client.get(GEOCODING_URL, params={"name": city, "count": 1, "language": "en"})
    resp.raise_for_status()
    data = resp.json()
    results = data.get("results")
    if not results:
        raise ValueError(f"Could not find location: {city}")
    r = results[0]
    return Location(
        name=r["name"],
        latitude=r["latitude"],
        longitude=r["longitude"],
        country=r.get("country", ""),
        admin1=r.get("admin1", ""),
    )


async def reverse_geocode(lat: float, lon: float, client: httpx.AsyncClient) -> Location:
    resp = await client.get(
        NOMINATIM_URL,
        params={"lat": lat, "lon": lon, "format": "json"},
        headers={"User-Agent": "weather-cmd/0.1"},
    )
    resp.raise_for_status()
    data = resp.json()
    addr = data.get("address", {})
    name = addr.get("city") or addr.get("town") or addr.get("village") or data.get("display_name", "Unknown")
    return Location(
        name=name,
        latitude=lat,
        longitude=lon,
        country=addr.get("country", ""),
        admin1=addr.get("state", ""),
    )


async def geocode_ip(client: httpx.AsyncClient) -> Location:
    resp = await client.get(IP_URL, timeout=5.0)
    resp.raise_for_status()
    data = resp.json()
    return Location(
        name=data.get("city", "Unknown"),
        latitude=data["latitude"],
        longitude=data["longitude"],
        country=data.get("country_name", ""),
        admin1=data.get("region", ""),
    )


async def resolve_location(
    city: str | None = None,
    coords: tuple[float, float] | None = None,
    client: httpx.AsyncClient | None = None,
) -> Location:
    own_client = client is None
    if own_client:
        client = httpx.AsyncClient()
    try:
        if city:
            return await geocode_city(city, client)
        if coords:
            return await reverse_geocode(coords[0], coords[1], client)
        return await geocode_ip(client)
    finally:
        if own_client:
            await client.aclose()
