"""Formatting helpers for weather display values."""

from __future__ import annotations


def fmt_temp(value: float, units: str = "imperial") -> str:
    if units == "metric":
        return f"{value:.0f}\u00b0C"
    return f"{value:.0f}\u00b0F"


def fmt_wind(speed: float, units: str = "imperial") -> str:
    if units == "metric":
        return f"{speed:.0f} km/h"
    return f"{speed:.0f} mph"


def fmt_precip(mm: float, units: str = "imperial") -> str:
    if units == "metric":
        return f"{mm:.1f} mm"
    inches = mm / 25.4
    return f"{inches:.2f} in"


def fmt_snow(cm: float, units: str = "imperial") -> str:
    if units == "metric":
        return f"{cm:.1f} cm"
    inches = cm / 2.54
    return f"{inches:.1f} in"


def fmt_visibility(meters: float, units: str = "imperial") -> str:
    if units == "metric":
        km = meters / 1000
        return f"{km:.1f} km"
    miles = meters / 1609.344
    return f"{miles:.1f} mi"


def fmt_percent(value: float) -> str:
    return f"{value:.0f}%"


def fmt_uv(value: float) -> str:
    level = "Low"
    if value >= 11:
        level = "Extreme"
    elif value >= 8:
        level = "Very High"
    elif value >= 6:
        level = "High"
    elif value >= 3:
        level = "Moderate"
    return f"{value:.0f} ({level})"


def wind_direction_arrow(degrees: int) -> str:
    arrows = ["\u2191", "\u2197", "\u2192", "\u2198", "\u2193", "\u2199", "\u2190", "\u2196"]
    index = round(degrees / 45) % 8
    return arrows[index]


def clean_nulls(values: list[float | None], default: float = 0.0) -> list[float]:
    return [v if v is not None else default for v in values]


def hour_label(hour: int) -> str:
    if hour == 0:
        return "12AM"
    if hour == 12:
        return "12PM"
    if hour < 12:
        return f"{hour}AM"
    return f"{hour - 12}PM"
