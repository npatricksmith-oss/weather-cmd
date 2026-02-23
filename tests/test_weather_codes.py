"""Tests for WMO weather code mappings."""

from weather_cmd.utils.weather_codes import get_weather_description, get_weather_emoji


def test_clear_sky():
    assert get_weather_emoji(0) == "\u2600\ufe0f"
    assert get_weather_description(0) == "Clear sky"


def test_thunderstorm():
    assert get_weather_description(95) == "Thunderstorm"


def test_unknown_code():
    assert get_weather_description(999) == "Unknown"
    assert get_weather_emoji(999) == "\u2753"


def test_all_codes_have_both_fields():
    from weather_cmd.utils.weather_codes import WMO_CODES

    for code, (emoji, desc) in WMO_CODES.items():
        assert isinstance(emoji, str) and len(emoji) > 0
        assert isinstance(desc, str) and len(desc) > 0
