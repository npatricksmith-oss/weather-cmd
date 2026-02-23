"""7-day forecast table and weekly charts."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widget import Widget
from textual.widgets import DataTable, Label, Static
from textual_plotext import PlotextPlot

from weather_cmd.models import DailyForecast, ForecastPeriod, WeatherData
from weather_cmd.utils.formatting import fmt_percent, fmt_precip, fmt_snow, fmt_temp
from weather_cmd.utils.weather_codes import get_weather_description, get_weather_emoji


class DailyView(Widget):
    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Label("7-Day Summary:", id="forecast-label")
            yield Static("", id="text-forecast-7day")
            yield DataTable(id="daily-table")
            yield Label("Detailed Forecast:", id="detailed-label")
            yield Static("", id="detailed-forecast")
            yield PlotextPlot(id="weekly-temp-plot")
            yield PlotextPlot(id="weekly-precip-plot")

    def on_mount(self) -> None:
        table = self.query_one("#daily-table", DataTable)
        table.add_columns("Day", "", "Condition", "High", "Low", "Precip", "Snow", "Precip %")

    def update_data(self, data: WeatherData, units: str = "imperial") -> None:
        daily = data.daily
        table = self.query_one("#daily-table", DataTable)
        table.clear()

        # Update detailed forecast
        detailed_text = self._format_detailed_forecast(data.detailed_forecast)
        self.query_one("#detailed-forecast", Static).update(detailed_text)

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
            precip_prob = fmt_percent(daily.precipitation_probability_max[i]) if i < len(daily.precipitation_probability_max) else "-"
            table.add_row(day_name, emoji, desc, high, low, precip, snow, precip_prob)

        self._draw_weekly_temp(day_labels, daily, units)
        self._draw_weekly_precip(day_labels, daily, units)

        # Update 7-day text forecast if available
        if data.text_forecast:
            self.query_one("#text-forecast-7day", Static).update(data.text_forecast)
        else:
            self.query_one("#text-forecast-7day", Static).update("(No extended forecast available)")

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

        # Convert to inches for imperial units
        precip_data = daily.precipitation_sum[: len(x)]
        if units == "imperial":
            precip_data = [p / 25.4 for p in precip_data]  # mm to inches
            unit_label = "in"
            title = "Weekly Precipitation (in)"
        else:
            unit_label = "mm"
            title = "Weekly Precipitation (mm)"

        plt.bar(x, precip_data, color="blue", width=0.6)
        plt.xticks(x, labels)
        plt.title(title)
        plt.ylabel(unit_label)
        self.query_one("#weekly-precip-plot", PlotextPlot).refresh()

    def _format_detailed_forecast(self, periods: list[ForecastPeriod]) -> str:
        """Format detailed forecast periods for display as a table."""
        if not periods:
            return "(No detailed forecast available)"

        lines = []

        # Add header separator
        lines.append("─" * 120)

        for i, period in enumerate(periods):
            # Period name column (20 chars wide, bold)
            name = period.name.ljust(20)
            # Detailed forecast (fill the rest of the line)
            forecast = period.detailed_forecast

            # Format: Bold period name followed by forecast text
            lines.append(f"  {name}  {forecast}")

            # Add separator between periods
            if i < len(periods) - 1:
                lines.append("─" * 120)

        # Add footer separator
        lines.append("─" * 120)

        return "\n".join(lines)
