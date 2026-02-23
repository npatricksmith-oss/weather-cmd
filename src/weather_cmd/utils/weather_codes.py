"""WMO weather interpretation codes to emoji and description mapping."""

WMO_CODES: dict[int, tuple[str, str]] = {
    0: ("\u2600\ufe0f", "Clear sky"),
    1: ("\U0001f324\ufe0f", "Mainly clear"),
    2: ("\u26c5", "Partly cloudy"),
    3: ("\u2601\ufe0f", "Overcast"),
    45: ("\U0001f32b\ufe0f", "Fog"),
    48: ("\U0001f32b\ufe0f", "Depositing rime fog"),
    51: ("\U0001f326\ufe0f", "Light drizzle"),
    53: ("\U0001f326\ufe0f", "Moderate drizzle"),
    55: ("\U0001f326\ufe0f", "Dense drizzle"),
    56: ("\U0001f327\ufe0f", "Light freezing drizzle"),
    57: ("\U0001f327\ufe0f", "Dense freezing drizzle"),
    61: ("\U0001f327\ufe0f", "Slight rain"),
    63: ("\U0001f327\ufe0f", "Moderate rain"),
    65: ("\U0001f327\ufe0f", "Heavy rain"),
    66: ("\U0001f327\ufe0f", "Light freezing rain"),
    67: ("\U0001f327\ufe0f", "Heavy freezing rain"),
    71: ("\U0001f328\ufe0f", "Slight snowfall"),
    73: ("\U0001f328\ufe0f", "Moderate snowfall"),
    75: ("\U0001f328\ufe0f", "Heavy snowfall"),
    77: ("\u2744\ufe0f", "Snow grains"),
    80: ("\U0001f326\ufe0f", "Slight rain showers"),
    81: ("\U0001f326\ufe0f", "Moderate rain showers"),
    82: ("\u26c8\ufe0f", "Violent rain showers"),
    85: ("\U0001f328\ufe0f", "Slight snow showers"),
    86: ("\U0001f328\ufe0f", "Heavy snow showers"),
    95: ("\u26a1", "Thunderstorm"),
    96: ("\u26a1", "Thunderstorm with slight hail"),
    99: ("\u26a1", "Thunderstorm with heavy hail"),
}


def get_weather_emoji(code: int) -> str:
    return WMO_CODES.get(code, ("\u2753", "Unknown"))[0]


def get_weather_description(code: int) -> str:
    return WMO_CODES.get(code, ("\u2753", "Unknown"))[1]
