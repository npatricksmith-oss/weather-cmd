"""Current conditions dashboard widget."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Label, Static

from weather_cmd.models import CurrentConditions, DailyForecast, NOAAAlert, WeatherData
from weather_cmd.utils.formatting import (
    fmt_percent,
    fmt_temp,
    fmt_visibility,
    fmt_wind,
    wind_direction_arrow,
)
from weather_cmd.utils.weather_codes import get_weather_description, get_weather_emoji


class AlertBanner(Static):
    DEFAULT_CSS = """
    AlertBanner {
        background: $error;
        color: $text;
        text-style: bold;
        padding: 0 1;
    }
    AlertBanner.safe {
        background: $success;
    }
    """

    def set_alerts(self, alerts: list[NOAAAlert]) -> None:
        if alerts:
            events = ", ".join(a.event for a in alerts[:3])
            suffix = f" (+{len(alerts) - 3} more)" if len(alerts) > 3 else ""
            self.update(f"\u26a0 ACTIVE ALERTS: {events}{suffix}")
            self.remove_class("safe")
        else:
            self.update("\u2713 No hazardous warnings active")
            self.add_class("safe")


class Dashboard(Widget):
    def compose(self) -> ComposeResult:
        yield AlertBanner(id="alert-banner")
        with Horizontal(id="dashboard-main"):
            with Vertical(id="current-hero"):
                yield Label("", id="hero-emoji")
                yield Label("", id="hero-desc")
                yield Label("", id="hero-temp")
                yield Label("", id="hero-feels")
            with Vertical(id="current-details"):
                yield Label("", id="detail-humidity")
                yield Label("", id="detail-wind")
                yield Label("", id="detail-visibility")
                yield Label("", id="detail-cloud")
                yield Label("", id="detail-precip")
            with Vertical(id="current-today"):
                yield Label("", id="detail-high-low")
                yield Label("", id="detail-sunrise")
                yield Label("", id="detail-sunset")
                yield Label("", id="detail-county")
        yield Static("", id="text-forecast")

    def update_data(self, data: WeatherData, units: str = "imperial") -> None:
        cur = data.current
        daily = data.daily
        alerts = data.alerts

        self.query_one("#alert-banner", AlertBanner).set_alerts(alerts)

        emoji = get_weather_emoji(cur.weather_code)
        desc = get_weather_description(cur.weather_code)

        self.query_one("#hero-emoji", Label).update(emoji)
        self.query_one("#hero-desc", Label).update(desc)
        self.query_one("#hero-temp", Label).update(fmt_temp(cur.temperature, units))
        self.query_one("#hero-feels", Label).update(f"Feels like {fmt_temp(cur.apparent_temperature, units)}")

        arrow = wind_direction_arrow(cur.wind_direction)
        self.query_one("#detail-humidity", Label).update(f"Humidity: {fmt_percent(cur.humidity)}")
        self.query_one("#detail-wind", Label).update(
            f"Wind: {fmt_wind(cur.wind_speed, units)} {arrow}  Gusts: {fmt_wind(cur.wind_gusts, units)}"
        )
        self.query_one("#detail-visibility", Label).update(f"Visibility: {fmt_visibility(cur.visibility, units)}")
        self.query_one("#detail-cloud", Label).update(f"Cloud Cover: {fmt_percent(cur.cloud_cover)}")
        self.query_one("#detail-precip", Label).update(f"Precipitation: {cur.precipitation:.1f} mm")

        if daily.dates:
            high = fmt_temp(daily.temp_max[0], units) if daily.temp_max else "-"
            low = fmt_temp(daily.temp_min[0], units) if daily.temp_min else "-"
            self.query_one("#detail-high-low", Label).update(f"Today: {high} / {low}")
            if daily.sunrise:
                self.query_one("#detail-sunrise", Label).update(f"Sunrise: {daily.sunrise[0][-5:]}")
            if daily.sunset:
                self.query_one("#detail-sunset", Label).update(f"Sunset: {daily.sunset[0][-5:]}")

        # Update county forecast
        if data.county:
            self.query_one("#detail-county", Label).update(f"County: {data.county}")
        else:
            self.query_one("#detail-county", Label).update("")

        # Update text forecast
        if data.text_forecast:
            self.query_one("#text-forecast", Static).update(data.text_forecast)
        else:
            self.query_one("#text-forecast", Static).update("(No text forecast available)")
