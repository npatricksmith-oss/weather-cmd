from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Location:
    name: str
    latitude: float
    longitude: float
    country: str = ""
    admin1: str = ""  # state/province

    @property
    def display_name(self) -> str:
        parts = [self.name]
        if self.admin1:
            parts.append(self.admin1)
        if self.country:
            parts.append(self.country)
        return ", ".join(parts)


@dataclass
class CurrentConditions:
    temperature: float
    apparent_temperature: float
    humidity: float
    wind_speed: float
    wind_gusts: float
    wind_direction: int
    weather_code: int
    cloud_cover: float
    visibility: float
    precipitation: float


@dataclass
class HourlyForecast:
    times: list[datetime] = field(default_factory=list)
    temperature: list[float] = field(default_factory=list)
    apparent_temperature: list[float] = field(default_factory=list)
    humidity: list[float] = field(default_factory=list)
    precipitation_probability: list[float] = field(default_factory=list)
    precipitation: list[float] = field(default_factory=list)
    snowfall: list[float] = field(default_factory=list)
    weather_code: list[int] = field(default_factory=list)
    cloud_cover: list[float] = field(default_factory=list)
    wind_speed: list[float] = field(default_factory=list)
    wind_gusts: list[float] = field(default_factory=list)
    visibility: list[float] = field(default_factory=list)


@dataclass
class DailyForecast:
    dates: list[datetime] = field(default_factory=list)
    weather_code: list[int] = field(default_factory=list)
    temp_max: list[float] = field(default_factory=list)
    temp_min: list[float] = field(default_factory=list)
    precipitation_sum: list[float] = field(default_factory=list)
    snowfall_sum: list[float] = field(default_factory=list)
    sunrise: list[str] = field(default_factory=list)
    sunset: list[str] = field(default_factory=list)
    uv_index_max: list[float] = field(default_factory=list)
    precipitation_probability_max: list[float] = field(default_factory=list)


@dataclass
class NOAAAlert:
    event: str
    headline: str
    description: str
    severity: str  # Extreme, Severe, Moderate, Minor, Unknown
    urgency: str
    onset: str
    expires: str
    sender_name: str


@dataclass
class ForecastPeriod:
    name: str
    detailed_forecast: str


@dataclass
class WeatherData:
    location: Location
    current: CurrentConditions
    hourly: HourlyForecast
    daily: DailyForecast
    alerts: list[NOAAAlert] = field(default_factory=list)
    text_forecast: str = ""
    county: str = ""
    detailed_forecast: list[ForecastPeriod] = field(default_factory=list)
    radar_image: bytes | None = None
    fetched_at: datetime = field(default_factory=datetime.now)
