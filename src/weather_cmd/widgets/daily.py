"""7-day forecast table and weekly charts."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widget import Widget
from textual.widgets import DataTable
from textual_plotext import PlotextPlot

from weather_cmd.models import DailyForecast
from weather_cmd.utils.formatting import fmt_precip, fmt_snow, fmt_temp, fmt_uv
from weather_cmd.utils.weather_codes import get_weather_description, get_weather_emoji


class DailyView(Widget):
    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield DataTable(id="daily-table")
            yield PlotextPlot(id="weekly-temp-plot")
            yield PlotextPlot(id="weekly-precip-plot")

    def on_mount(self) -> None:
        table = self.query_one("#daily-table", DataTable)
        table.add_columns("Day", "", "Condition", "High", "Low", "Precip", "Snow", "UV")

    def update_data(self, daily: DailyForecast, units: str = "imperial") -> None:
        table = self.query_one("#daily-table", DataTable)
        table.clear()

        day_labels = []
        for i, dt in enumerate(daily.dates):
            day_name = dt.strftime("%a %m/%d") if i > 0 else "Today"
            day_labels.append(day_name if i > 0 else "Today")
            code = daily.weather_code[i] if i < len(daily.weather_code) else 0
            emoji = get_weather_emoji(code)
            desc = get_weather_description(code)
            high = fmt_temp(daily.temp_max[i], units) if i < len(daily.temp_max) else "-"
            low = fmt_temp(daily.temp_min[i], units) if i < len(daily.temp_min) else "-"
            precip = fmt_precip(daily.precipitation_sum[i], units) if i < len(daily.precipitation_sum) else "-"
            snow = fmt_snow(daily.snowfall_sum[i], units) if i < len(daily.snowfall_sum) else "-"
            uv = fmt_uv(daily.uv_index_max[i]) if i < len(daily.uv_index_max) else "-"
            table.add_row(day_name, emoji, desc, high, low, precip, snow, uv)

        self._draw_weekly_temp(day_labels, daily, units)
        self._draw_weekly_precip(day_labels, daily, units)

    def _draw_weekly_temp(self, labels: list[str], daily: DailyForecast, units: str) -> None:
        plt = self.query_one("#weekly-temp-plot", PlotextPlot).plt
        plt.clf()
        x = list(range(len(labels)))
        plt.multiple_bar(
            x,
            [daily.temp_max[: len(x)], daily.temp_min[: len(x)]],
            labels=["High", "Low"],
            color=["orange", "cyan"],
        )
        plt.xticks(x, labels)
        unit = "\u00b0F" if units == "imperial" else "\u00b0C"
        plt.title(f"Weekly High / Low ({unit})")
        self.query_one("#weekly-temp-plot", PlotextPlot).refresh()

    def _draw_weekly_precip(self, labels: list[str], daily: DailyForecast, units: str) -> None:
        plt = self.query_one("#weekly-precip-plot", PlotextPlot).plt
        plt.clf()
        x = list(range(len(labels)))
        plt.bar(x, daily.precipitation_sum[: len(x)], color="blue", width=0.6)
        plt.xticks(x, labels)
        plt.title("Weekly Precipitation (mm)")
        plt.ylabel("mm")
        self.query_one("#weekly-precip-plot", PlotextPlot).refresh()
