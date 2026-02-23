"""NOAA alerts detail widget."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label, RichLog

from weather_cmd.models import NOAAAlert

SEVERITY_COLORS = {
    "Extreme": "red",
    "Severe": "dark_orange",
    "Moderate": "yellow",
    "Minor": "cyan",
    "Unknown": "white",
}


class AlertsView(Widget):
    def compose(self) -> ComposeResult:
        yield Label("Weather Alerts", id="alerts-title")
        yield RichLog(id="alerts-log", markup=True)

    def update_data(self, alerts: list[NOAAAlert]) -> None:
        log = self.query_one("#alerts-log", RichLog)
        log.clear()

        if not alerts:
            log.write("[dim]No active weather alerts.[/dim]")
            return

        for alert in alerts:
            color = SEVERITY_COLORS.get(alert.severity, "white")
            log.write(f"[bold {color}]{alert.event}[/bold {color}]")
            log.write(f"[bold]Severity:[/bold] {alert.severity}  |  [bold]Urgency:[/bold] {alert.urgency}")
            if alert.headline:
                log.write(f"[bold]Headline:[/bold] {alert.headline}")
            if alert.onset:
                log.write(f"[bold]Onset:[/bold] {alert.onset}")
            if alert.expires:
                log.write(f"[bold]Expires:[/bold] {alert.expires}")
            if alert.sender_name:
                log.write(f"[dim]Source: {alert.sender_name}[/dim]")
            log.write("")
            if alert.description:
                log.write(alert.description)
            log.write("\n" + "\u2500" * 60 + "\n")
