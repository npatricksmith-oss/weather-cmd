"""Primary forecast graph panels using textual-plotext."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label
from textual_plotext import PlotextPlot

from weather_cmd.models import HourlyForecast
from weather_cmd.utils.formatting import hour_label

RANGE_OPTIONS = [24, 48, 72]


class ForecastGraphs(Widget):
    hours: reactive[int] = reactive(48)

    def compose(self) -> ComposeResult:
        yield Label("", id="range-label")
        with VerticalScroll():
            yield PlotextPlot(id="temp-plot")
            yield PlotextPlot(id="precip-prob-plot")
            yield PlotextPlot(id="humidity-plot")
            yield PlotextPlot(id="snow-plot")
            yield PlotextPlot(id="wind-plot")
            yield PlotextPlot(id="cloud-plot")

    def on_mount(self) -> None:
        self._update_range_label()

    def _update_range_label(self) -> None:
        label = self.query_one("#range-label", Label)
        label.update(f"  Forecast: {self.hours}h  |  [ / ] to change range")

    def cycle_range(self, direction: int) -> None:
        idx = RANGE_OPTIONS.index(self.hours) if self.hours in RANGE_OPTIONS else 1
        idx = max(0, min(len(RANGE_OPTIONS) - 1, idx + direction))
        self.hours = RANGE_OPTIONS[idx]
        self._update_range_label()

    def update_data(self, hourly: HourlyForecast, units: str = "imperial") -> None:
        n = min(self.hours, len(hourly.times))
        if n == 0:
            return

        x = list(range(n))
        # Build x-axis labels every 6 hours
        xticks_pos = list(range(0, n, 6))
        xticks_labels = []
        for i in xticks_pos:
            t = hourly.times[i]
            lbl = hour_label(t.hour)
            if t.hour == 0 or i == 0:
                lbl = t.strftime("%a") + " " + lbl
            xticks_labels.append(lbl)

        temp_unit = "\u00b0F" if units == "imperial" else "\u00b0C"
        wind_unit = "mph" if units == "imperial" else "km/h"

        self._draw_temperature(x, hourly, n, xticks_pos, xticks_labels, temp_unit)
        self._draw_precip_prob(x, hourly, n, xticks_pos, xticks_labels)
        self._draw_humidity(x, hourly, n, xticks_pos, xticks_labels)
        self._draw_snowfall(x, hourly, n, xticks_pos, xticks_labels)
        self._draw_wind(x, hourly, n, xticks_pos, xticks_labels, wind_unit)
        self._draw_cloud(x, hourly, n, xticks_pos, xticks_labels)

    def _draw_temperature(self, x, hourly, n, xt_pos, xt_lbl, unit):
        plt = self.query_one("#temp-plot", PlotextPlot).plt
        plt.clf()
        plt.plot(x, hourly.temperature[:n], label=f"Temp ({unit})", color="orange")
        plt.plot(x, hourly.apparent_temperature[:n], label=f"Feels like ({unit})", color=[209, 154, 102])
        plt.xticks(xt_pos, xt_lbl)
        plt.title("Temperature")
        plt.ylabel(unit)
        self.query_one("#temp-plot", PlotextPlot).refresh()

    def _draw_precip_prob(self, x, hourly, n, xt_pos, xt_lbl):
        plt = self.query_one("#precip-prob-plot", PlotextPlot).plt
        plt.clf()
        plt.bar(x, hourly.precipitation_probability[:n], color="blue", width=0.8)
        plt.xticks(xt_pos, xt_lbl)
        plt.ylim(0, 100)
        plt.title("Precipitation Probability")
        plt.ylabel("%")
        self.query_one("#precip-prob-plot", PlotextPlot).refresh()

    def _draw_humidity(self, x, hourly, n, xt_pos, xt_lbl):
        plt = self.query_one("#humidity-plot", PlotextPlot).plt
        plt.clf()
        plt.plot(x, hourly.humidity[:n], color="cyan")
        plt.xticks(xt_pos, xt_lbl)
        plt.ylim(0, 100)
        plt.title("Humidity")
        plt.ylabel("%")
        self.query_one("#humidity-plot", PlotextPlot).refresh()

    def _draw_snowfall(self, x, hourly, n, xt_pos, xt_lbl):
        plt = self.query_one("#snow-plot", PlotextPlot).plt
        plt.clf()
        snow = hourly.snowfall[:n]
        plt.bar(x, snow, color=[173, 216, 230], width=0.8)
        plt.xticks(xt_pos, xt_lbl)
        plt.title("Snowfall")
        plt.ylabel("cm")
        self.query_one("#snow-plot", PlotextPlot).refresh()

    def _draw_wind(self, x, hourly, n, xt_pos, xt_lbl, unit):
        plt = self.query_one("#wind-plot", PlotextPlot).plt
        plt.clf()
        plt.plot(x, hourly.wind_speed[:n], label=f"Speed ({unit})", color="green")
        plt.plot(x, hourly.wind_gusts[:n], label=f"Gusts ({unit})", color="red")
        plt.xticks(xt_pos, xt_lbl)
        plt.title("Wind Speed")
        plt.ylabel(unit)
        self.query_one("#wind-plot", PlotextPlot).refresh()

    def _draw_cloud(self, x, hourly, n, xt_pos, xt_lbl):
        plt = self.query_one("#cloud-plot", PlotextPlot).plt
        plt.clf()
        plt.plot(x, hourly.cloud_cover[:n], color=[150, 150, 150], fillx=True)
        plt.xticks(xt_pos, xt_lbl)
        plt.ylim(0, 100)
        plt.title("Cloud Cover")
        plt.ylabel("%")
        self.query_one("#cloud-plot", PlotextPlot).refresh()
