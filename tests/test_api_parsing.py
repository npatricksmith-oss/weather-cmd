"""Tests for API client parsing with mocked responses."""

import httpx
import pytest
import respx

from weather_cmd.api.geocode import geocode_city, geocode_zipcode
from weather_cmd.api.noaa import fetch_alerts, fetch_forecast_fallback
from weather_cmd.api.openmeteo import fetch_forecast


@pytest.fixture
def async_client():
    return httpx.AsyncClient()


@respx.mock
@pytest.mark.asyncio
async def test_geocode_city():
    respx.get("https://geocoding-api.open-meteo.com/v1/search").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "Denver",
                        "latitude": 39.7392,
                        "longitude": -104.9903,
                        "country": "United States",
                        "admin1": "Colorado",
                    }
                ]
            },
        )
    )
    async with httpx.AsyncClient() as client:
        loc = await geocode_city("Denver", client)
    assert loc.name == "Denver"
    assert loc.admin1 == "Colorado"
    assert abs(loc.latitude - 39.7392) < 0.01


@respx.mock
@pytest.mark.asyncio
async def test_geocode_city_not_found():
    respx.get("https://geocoding-api.open-meteo.com/v1/search").mock(
        return_value=httpx.Response(200, json={})
    )
    async with httpx.AsyncClient() as client:
        with pytest.raises(ValueError, match="Could not find"):
            await geocode_city("xyznonexistent", client)


@respx.mock
@pytest.mark.asyncio
async def test_geocode_zipcode():
    route = respx.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": "10001", "count": "3", "language": "en", "countryCode": "US"},
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "New York",
                        "latitude": 40.7506,
                        "longitude": -73.9972,
                        "country": "United States",
                        "admin1": "New York",
                    }
                ]
            },
        )
    )
    async with httpx.AsyncClient() as client:
        loc = await geocode_zipcode("10001", client)
    assert route.called
    assert loc.name == "New York"
    assert loc.admin1 == "New York"
    assert abs(loc.latitude - 40.7506) < 0.01


@respx.mock
@pytest.mark.asyncio
async def test_geocode_zipcode_falls_back_without_us_match():
    us_route = respx.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": "75001", "count": "3", "language": "en", "countryCode": "US"},
    ).mock(return_value=httpx.Response(200, json={}))
    fallback_route = respx.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": "75001", "count": "1", "language": "en"},
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "Paris",
                        "latitude": 48.8647,
                        "longitude": 2.3314,
                        "country": "France",
                        "admin1": "Ile-de-France",
                    }
                ]
            },
        )
    )

    async with httpx.AsyncClient() as client:
        loc = await geocode_zipcode("75001", client)

    assert us_route.called
    assert fallback_route.called
    assert loc.name == "Paris"
    assert loc.country == "France"


@respx.mock
@pytest.mark.asyncio
async def test_geocode_zipcode_normalizes_zip_plus_four():
    route = respx.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": "10001", "count": "3", "language": "en", "countryCode": "US"},
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "New York",
                        "latitude": 40.7506,
                        "longitude": -73.9972,
                        "country": "United States",
                        "admin1": "New York",
                    }
                ]
            },
        )
    )

    async with httpx.AsyncClient() as client:
        loc = await geocode_zipcode("10001-1234", client)

    assert route.called
    assert loc.name == "New York"


@respx.mock
@pytest.mark.asyncio
async def test_geocode_zipcode_prefers_exact_us_postcode_match():
    route = respx.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": "13114", "count": "3", "language": "en", "countryCode": "US"},
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "Wrong Match",
                        "latitude": 42.0,
                        "longitude": -75.0,
                        "country": "United States",
                        "admin1": "New York",
                        "postcodes": ["13115"],
                    },
                    {
                        "name": "Mexico",
                        "latitude": 43.45951,
                        "longitude": -76.22882,
                        "country": "United States",
                        "admin1": "New York",
                        "postcodes": ["13114"],
                    },
                ]
            },
        )
    )

    async with httpx.AsyncClient() as client:
        loc = await geocode_zipcode("13114", client)

    assert route.called
    assert loc.name == "Mexico"
    assert loc.admin1 == "New York"


@respx.mock
@pytest.mark.asyncio
async def test_fetch_forecast():
    hourly_times = [f"2025-01-01T{h:02d}:00" for h in range(24)]
    daily_times = ["2025-01-01"]

    respx.get("https://api.open-meteo.com/v1/forecast").mock(
        return_value=httpx.Response(
            200,
            json={
                "current": {
                    "temperature_2m": 45.0,
                    "apparent_temperature": 40.0,
                    "relative_humidity_2m": 55,
                    "wind_speed_10m": 10,
                    "wind_gusts_10m": 20,
                    "wind_direction_10m": 180,
                    "weather_code": 2,
                    "cloud_cover": 50,
                    "visibility": 16000,
                    "precipitation": 0,
                },
                "hourly": {
                    "time": hourly_times,
                    "temperature_2m": [45 + i * 0.5 for i in range(24)],
                    "apparent_temperature": [40 + i * 0.5 for i in range(24)],
                    "relative_humidity_2m": [55] * 24,
                    "precipitation_probability": [10] * 24,
                    "precipitation": [0] * 24,
                    "snowfall": [0] * 24,
                    "weather_code": [2] * 24,
                    "cloud_cover": [50] * 24,
                    "wind_speed_10m": [10] * 24,
                    "wind_gusts_10m": [20] * 24,
                    "visibility": [16000] * 24,
                },
                "daily": {
                    "time": daily_times,
                    "temperature_2m_max": [55],
                    "temperature_2m_min": [35],
                    "precipitation_sum": [0],
                    "snowfall_sum": [0],
                    "sunrise": ["2025-01-01T07:15"],
                    "sunset": ["2025-01-01T17:00"],
                    "uv_index_max": [3],
                    "weather_code": [2],
                    "precipitation_probability_max": [10],
                },
            },
        )
    )

    async with httpx.AsyncClient() as client:
        current, hourly, daily = await fetch_forecast(39.74, -104.99, client)

    assert current.temperature == 45.0
    assert len(hourly.times) == 24
    assert daily.temp_max[0] == 55


@respx.mock
@pytest.mark.asyncio
async def test_fetch_alerts_non_us():
    respx.get("https://api.weather.gov/alerts/active").mock(
        return_value=httpx.Response(404)
    )
    async with httpx.AsyncClient() as client:
        alerts = await fetch_alerts(51.5, -0.12, client)
    assert alerts == []


@respx.mock
@pytest.mark.asyncio
async def test_fetch_alerts_with_data():
    respx.get("https://api.weather.gov/alerts/active").mock(
        return_value=httpx.Response(
            200,
            json={
                "features": [
                    {
                        "properties": {
                            "event": "Winter Storm Warning",
                            "headline": "Heavy snow expected",
                            "description": "8-12 inches of snow expected.",
                            "severity": "Severe",
                            "urgency": "Expected",
                            "onset": "2025-01-02T06:00:00",
                            "expires": "2025-01-03T06:00:00",
                            "senderName": "NWS Boulder",
                        }
                    }
                ]
            },
        )
    )
    async with httpx.AsyncClient() as client:
        alerts = await fetch_alerts(39.74, -104.99, client)
    assert len(alerts) == 1
    assert alerts[0].event == "Winter Storm Warning"
    assert alerts[0].severity == "Severe"


@respx.mock
@pytest.mark.asyncio
async def test_fetch_forecast_fallback_from_noaa():
    respx.get("https://api.weather.gov/points/43.4595,-76.2288").mock(
        return_value=httpx.Response(
            200,
            json={
                "properties": {
                    "forecast": "https://api.weather.gov/gridpoints/BUF/121,85/forecast",
                    "forecastHourly": "https://api.weather.gov/gridpoints/BUF/121,85/forecast/hourly",
                }
            },
        )
    )
    respx.get("https://api.weather.gov/gridpoints/BUF/121,85/forecast/hourly").mock(
        return_value=httpx.Response(
            200,
            json={
                "properties": {
                    "periods": [
                        {
                            "startTime": "2026-04-07T01:00:00-04:00",
                            "temperature": 32,
                            "temperatureUnit": "F",
                            "probabilityOfPrecipitation": {"value": 30},
                            "relativeHumidity": {"value": 78},
                            "windSpeed": "3 mph",
                            "windDirection": "S",
                            "shortForecast": "Chance Snow Showers",
                            "isDaytime": False,
                        },
                        {
                            "startTime": "2026-04-07T02:00:00-04:00",
                            "temperature": 31,
                            "temperatureUnit": "F",
                            "probabilityOfPrecipitation": {"value": 20},
                            "relativeHumidity": {"value": 80},
                            "windSpeed": "4 mph",
                            "windDirection": "SW",
                            "shortForecast": "Mostly Cloudy",
                            "isDaytime": False,
                        },
                    ]
                }
            },
        )
    )
    respx.get("https://api.weather.gov/gridpoints/BUF/121,85/forecast").mock(
        return_value=httpx.Response(
            200,
            json={
                "properties": {
                    "periods": [
                        {
                            "startTime": "2026-04-07T06:00:00-04:00",
                            "temperature": 40,
                            "temperatureUnit": "F",
                            "probabilityOfPrecipitation": {"value": 50},
                            "shortForecast": "Partly Sunny",
                            "isDaytime": True,
                        },
                        {
                            "startTime": "2026-04-07T18:00:00-04:00",
                            "temperature": 28,
                            "temperatureUnit": "F",
                            "probabilityOfPrecipitation": {"value": 10},
                            "shortForecast": "Mostly Clear",
                            "isDaytime": False,
                        },
                        {
                            "startTime": "2026-04-08T06:00:00-04:00",
                            "temperature": 42,
                            "temperatureUnit": "F",
                            "probabilityOfPrecipitation": {"value": 20},
                            "shortForecast": "Rain Showers",
                            "isDaytime": True,
                        },
                    ]
                }
            },
        )
    )

    async with httpx.AsyncClient() as client:
        current, hourly, daily = await fetch_forecast_fallback(43.4595, -76.2288, client)

    assert current.temperature == 32
    assert current.humidity == 78
    assert current.weather_code == 71
    assert len(hourly.times) == 2
    assert hourly.wind_speed[1] == 4
    assert len(daily.dates) == 2
    assert daily.temp_max[0] == 40
    assert daily.temp_min[0] == 28
    assert daily.weather_code[0] == 2
    assert daily.weather_code[1] == 61
