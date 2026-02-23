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
            yield PlotextPlot(id="precip-amount-plot")
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
        precip_unit = "in" if units == "imperial" else "mm"
        snow_unit = "in" if units == "imperial" else "cm"

        self._draw_temperature(x, hourly, n, xticks_pos, xticks_labels, temp_unit)
        self._draw_precip_prob(x, hourly, n, xticks_pos, xticks_labels)
        self._draw_precip_amount(x, hourly, n, xticks_pos, xticks_labels, precip_unit, units)
        self._draw_humidity(x, hourly, n, xticks_pos, xticks_labels)
        self._draw_snowfall(x, hourly, n, xticks_pos, xticks_labels, snow_unit, units)
        self._draw_wind(x, hourly, n, xticks_pos, xticks_labels, wind_unit)
        self._draw_cloud(x, hourly, n, xticks_pos, xticks_labels)

    def _draw_temperature(self, x, hourly, n, xt_pos, xt_lbl, unit):
        plt = self.query_one("#temp-plot", PlotextPlot).plt
        plt.clf()
        temp_rounded = [round(t) for t in hourly.temperature[:n]]
        feels_rounded = [round(f) for f in hourly.apparent_temperature[:n]]
        plt.plot(x, temp_rounded, label=f"Temp ({unit})", color=[255, 255, 0])
        plt.plot(x, feels_rounded, label=f"Feels like ({unit})", color="orange")
        plt.xticks(xt_pos, xt_lbl)
        plt.title(f"Temperature ({unit})")
        plt.ylabel(f"({unit})")
        # Set y-axis ticks with integer formatting
        all_temps = temp_rounded + feels_rounded
        if all_temps:
            ymin, ymax = int(min(all_temps)), int(max(all_temps))
            step = max(1, (ymax - ymin) // 5)
            yticks = list(range(ymin, ymax + 1, step))
            plt.yticks(yticks, [str(int(y)) for y in yticks])
        self.query_one("#temp-plot", PlotextPlot).refresh()

    def _draw_precip_prob(self, x, hourly, n, xt_pos, xt_lbl):
        plt = self.query_one("#precip-prob-plot", PlotextPlot).plt
        plt.clf()
        precip_rounded = [round(p) for p in hourly.precipitation_probability[:n]]
        plt.plot(x, precip_rounded, color="bright_blue")
        plt.xticks(xt_pos, xt_lbl)
        plt.ylim(0, 100)
        plt.title("Precipitation Probability %")
        plt.ylabel("%")
        plt.yfrequency(11)
        self.query_one("#precip-prob-plot", PlotextPlot).refresh()

    def _draw_precip_amount(self, x, hourly, n, xt_pos, xt_lbl, unit, units):
        plt = self.query_one("#precip-amount-plot", PlotextPlot).plt
        plt.clf()
        precip_data = hourly.precipitation[:n]
        # Convert to imperial if needed
        if units == "imperial":
            precip_data = [p / 25.4 for p in precip_data]
        # Round to 2 decimals for precipitation
        precip_rounded = [round(p, 2) for p in precip_data]
        plt.bar(x, precip_rounded, color="bright_blue", width=0.8)
        plt.xticks(xt_pos, xt_lbl)
        plt.title(f"Precipitation Amount ({unit})")
        plt.ylabel(f"({unit})")
        # Set y-axis ticks with 2 decimal formatting
        if precip_rounded:
            ymax = max(precip_rounded)
            step = max(0.01, ymax / 5) if ymax > 0 else 0.01
            yticks = [round(i * step, 2) for i in range(int(ymax / step) + 2)]
            plt.yticks(yticks, [f"{y:.2f}" for y in yticks])
        self.query_one("#precip-amount-plot", PlotextPlot).refresh()

    def _draw_humidity(self, x, hourly, n, xt_pos, xt_lbl):
        plt = self.query_one("#humidity-plot", PlotextPlot).plt
        plt.clf()
        humidity_rounded = [round(h) for h in hourly.humidity[:n]]
        plt.plot(x, humidity_rounded, color="bright_green")
        plt.xticks(xt_pos, xt_lbl)
        plt.ylim(0, 100)
        plt.title("Humidity %")
        plt.ylabel("%")
        plt.yfrequency(11)
        self.query_one("#humidity-plot", PlotextPlot).refresh()

    def _draw_snowfall(self, x, hourly, n, xt_pos, xt_lbl, unit, units):
        plt = self.query_one("#snow-plot", PlotextPlot).plt
        plt.clf()
        snow_data = hourly.snowfall[:n]
        # Convert to imperial if needed
        if units == "imperial":
            snow_data = [s / 2.54 for s in snow_data]
        # Round to 2 decimals for snowfall
        snow_rounded = [round(s, 2) for s in snow_data]
        plt.bar(x, snow_rounded, color="white", width=0.8)
        plt.xticks(xt_pos, xt_lbl)
        plt.title(f"Snowfall ({unit})")
        plt.ylabel(f"({unit})")
        # Set y-axis ticks with 2 decimal formatting
        if snow_rounded:
            ymax = max(snow_rounded)
            step = max(0.01, ymax / 5) if ymax > 0 else 0.01
            yticks = [round(i * step, 2) for i in range(int(ymax / step) + 2)]
            plt.yticks(yticks, [f"{y:.2f}" for y in yticks])
        self.query_one("#snow-plot", PlotextPlot).refresh()

    def _draw_wind(self, x, hourly, n, xt_pos, xt_lbl, unit):
        plt = self.query_one("#wind-plot", PlotextPlot).plt
        plt.clf()
        speed_rounded = [round(s) for s in hourly.wind_speed[:n]]
        gusts_rounded = [round(g) for g in hourly.wind_gusts[:n]]
        plt.plot(x, speed_rounded, label=f"Speed ({unit})", color="bright_blue")
        plt.plot(x, gusts_rounded, label=f"Gusts ({unit})", color="bright_cyan")
        plt.xticks(xt_pos, xt_lbl)
        plt.title(f"Wind Speed ({unit})")
        plt.ylabel(f"({unit})")
        # Set y-axis ticks with integer formatting
        all_winds = speed_rounded + gusts_rounded
        if all_winds:
            ymin, ymax = int(min(all_winds)), int(max(all_winds))
            step = max(1, (ymax - ymin) // 5)
            yticks = list(range(ymin, ymax + 1, step))
            plt.yticks(yticks, [str(int(y)) for y in yticks])
        self.query_one("#wind-plot", PlotextPlot).refresh()

    def _draw_cloud(self, x, hourly, n, xt_pos, xt_lbl):
        plt = self.query_one("#cloud-plot", PlotextPlot).plt
        plt.clf()
        cloud_rounded = [round(c) for c in hourly.cloud_cover[:n]]
        plt.plot(x, cloud_rounded, color=[150, 150, 150], fillx=True)
        plt.xticks(xt_pos, xt_lbl)
        plt.ylim(0, 100)
        plt.title("Cloud Cover %")
        plt.ylabel("%")
        plt.yfrequency(11)
        self.query_one("#cloud-plot", PlotextPlot).refresh()
