"""Textual App: tab navigation, data orchestration, async fetching."""

from __future__ import annotations

from pathlib import Path

import httpx
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header, Label, LoadingIndicator, TabbedContent, TabPane

from weather_cmd.api.geocode import resolve_location
from weather_cmd.api.noaa import fetch_alerts
from weather_cmd.api.openmeteo import fetch_forecast
from weather_cmd.api.rainviewer import fetch_radar
from weather_cmd.models import Location, WeatherData
from weather_cmd.widgets.alerts import AlertsView
from weather_cmd.widgets.dashboard import Dashboard
from weather_cmd.widgets.daily import DailyView
from weather_cmd.widgets.graphs import ForecastGraphs
from weather_cmd.widgets.radar import RadarView

CSS_PATH = Path(__file__).parent / "app.tcss"


class WeatherApp(App):
    TITLE = "weather-cmd"
    CSS_PATH = CSS_PATH

    BINDINGS = [
        Binding("1", "tab('graphs')", "Graphs", show=True),
        Binding("2", "tab('dashboard')", "Dashboard", show=True),
        Binding("3", "tab('daily')", "7-Day", show=True),
        Binding("4", "tab('radar')", "Radar", show=True),
        Binding("5", "tab('alerts')", "Alerts", show=True),
        Binding("r", "refresh_data", "Refresh", show=True),
        Binding("q", "quit", "Quit", show=True),
        Binding("[", "range_shrink", "Range -", show=False),
        Binding("]", "range_expand", "Range +", show=False),
    ]

    def __init__(
        self,
        city: str | None = None,
        coords: tuple[float, float] | None = None,
        units: str = "imperial",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._city = city
        self._coords = coords
        self._units = units
        self._weather_data: WeatherData | None = None
        self._location: Location | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("", id="header-bar")
        yield LoadingIndicator()
        with TabbedContent(id="tabs"):
            with TabPane("Graphs", id="graphs"):
                yield ForecastGraphs()
            with TabPane("Dashboard", id="dashboard"):
                yield Dashboard()
            with TabPane("7-Day", id="daily"):
                yield DailyView()
            with TabPane("Radar", id="radar"):
                yield RadarView()
            with TabPane("Alerts", id="alerts"):
                yield AlertsView()
        yield Footer()

    def on_mount(self) -> None:
        self.fetch_weather()
        self.set_interval(1800, self.fetch_weather)  # 30 min auto-refresh

    @property
    def loading_indicator(self) -> LoadingIndicator:
        return self.query_one(LoadingIndicator)

    def _set_loading(self, loading: bool) -> None:
        indicator = self.loading_indicator
        indicator.display = loading

    def action_tab(self, tab_id: str) -> None:
        tabs = self.query_one("#tabs", TabbedContent)
        tabs.active = tab_id

    def action_refresh_data(self) -> None:
        self.fetch_weather()

    def action_range_shrink(self) -> None:
        try:
            graphs = self.query_one(ForecastGraphs)
            graphs.cycle_range(-1)
            if self._weather_data:
                graphs.update_data(self._weather_data.hourly, self._units)
        except Exception:
            pass

    def action_range_expand(self) -> None:
        try:
            graphs = self.query_one(ForecastGraphs)
            graphs.cycle_range(1)
            if self._weather_data:
                graphs.update_data(self._weather_data.hourly, self._units)
        except Exception:
            pass

    @work(exclusive=True, thread=False)
    async def fetch_weather(self) -> None:
        self._set_loading(True)
        try:
            async with httpx.AsyncClient() as client:
                if self._location is None:
                    self._location = await resolve_location(
                        city=self._city,
                        coords=self._coords,
                        client=client,
                    )

                loc = self._location
                self.query_one("#header-bar", Label).update(
                    f"  {loc.display_name}  ({loc.latitude:.2f}, {loc.longitude:.2f})"
                )
                self.sub_title = loc.display_name

                current, hourly, daily = await fetch_forecast(
                    loc.latitude, loc.longitude, client, self._units
                )
                alerts = await fetch_alerts(loc.latitude, loc.longitude, client)

                radar_image: bytes | None = None
                try:
                    radar_image = await fetch_radar(loc.latitude, loc.longitude, client)
                except Exception:
                    pass

                self._weather_data = WeatherData(
                    location=loc,
                    current=current,
                    hourly=hourly,
                    daily=daily,
                    alerts=alerts,
                    radar_image=radar_image,
                )

                self._update_widgets()
        except Exception as e:
            self.notify(f"Error fetching weather: {e}", severity="error")
        finally:
            self._set_loading(False)

    def _update_widgets(self) -> None:
        data = self._weather_data
        if data is None:
            return

        self.query_one(ForecastGraphs).update_data(data.hourly, self._units)
        self.query_one(Dashboard).update_data(data, self._units)
        self.query_one(DailyView).update_data(data.daily, self._units)
        self.query_one(RadarView).update_data(data.radar_image)
        self.query_one(AlertsView).update_data(data.alerts)
