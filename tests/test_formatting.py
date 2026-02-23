"""Tests for formatting utilities."""

from weather_cmd.utils.formatting import (
    clean_nulls,
    fmt_percent,
    fmt_precip,
    fmt_snow,
    fmt_temp,
    fmt_uv,
    fmt_visibility,
    fmt_wind,
    hour_label,
    wind_direction_arrow,
)


def test_fmt_temp_imperial():
    assert fmt_temp(72.6, "imperial") == "73\u00b0F"


def test_fmt_temp_metric():
    assert fmt_temp(22.3, "metric") == "22\u00b0C"


def test_fmt_wind_imperial():
    assert fmt_wind(15.0, "imperial") == "15 mph"


def test_fmt_wind_metric():
    assert fmt_wind(24.0, "metric") == "24 km/h"


def test_fmt_precip_imperial():
    result = fmt_precip(25.4, "imperial")
    assert "1.00 in" == result


def test_fmt_precip_metric():
    assert fmt_precip(5.2, "metric") == "5.2 mm"


def test_fmt_snow_imperial():
    result = fmt_snow(2.54, "imperial")
    assert "1.0 in" == result


def test_fmt_snow_metric():
    assert fmt_snow(10.0, "metric") == "10.0 cm"


def test_fmt_visibility():
    assert fmt_visibility(1609.344, "imperial") == "1.0 mi"
    assert fmt_visibility(1000, "metric") == "1.0 km"


def test_fmt_percent():
    assert fmt_percent(85.0) == "85%"


def test_fmt_uv():
    assert "Low" in fmt_uv(2)
    assert "Moderate" in fmt_uv(4)
    assert "High" in fmt_uv(7)
    assert "Very High" in fmt_uv(9)
    assert "Extreme" in fmt_uv(12)


def test_wind_direction_arrow():
    assert wind_direction_arrow(0) == "\u2191"    # N
    assert wind_direction_arrow(90) == "\u2192"   # E
    assert wind_direction_arrow(180) == "\u2193"  # S
    assert wind_direction_arrow(270) == "\u2190"  # W


def test_clean_nulls():
    assert clean_nulls([1.0, None, 3.0]) == [1.0, 0.0, 3.0]
    assert clean_nulls([None, None], default=-1.0) == [-1.0, -1.0]


def test_hour_label():
    assert hour_label(0) == "12AM"
    assert hour_label(12) == "12PM"
    assert hour_label(3) == "3AM"
    assert hour_label(15) == "3PM"
