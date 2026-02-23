# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**weather-cmd** is a terminal-based weather application built with [Textual](https://textual.textualize.io/), a modern TUI framework for Python. It fetches weather data from multiple APIs (Open-Meteo, NOAA) and displays forecasts via graphs, daily summaries, weather alerts, and radar imagery.

- **Language**: Python 3.12+
- **Framework**: Textual (TUI)
- **Key Dependencies**: textual, textual-plotext (graphs), textual-image (radar), httpx (async HTTP), pillow (image handling)

## Architecture

The project follows a modular, layered design:

```
api/              - Data fetching clients (geocoding, weather APIs, alerts, radar)
  ├── geocode.py  - Resolves city names to coordinates
  ├── openmeteo.py - Open-Meteo weather API client
  ├── noaa.py     - NOAA alerts fetching
  └── rainviewer.py - Radar image fetching

models.py         - Dataclasses (Location, WeatherData, HourlyForecast, DailyForecast, NOAAAlert, CurrentConditions)

widgets/          - UI components (Textual widgets)
  ├── graphs.py   - ForecastGraphs: 6 simultaneous plotext charts (temp, feels-like, humidity, precip prob, cloud cover, wind)
  ├── dashboard.py - Current conditions overview
  ├── daily.py    - 7-day forecast view
  ├── radar.py    - Radar image widget
  └── alerts.py   - Active weather alerts list

utils/            - Utilities
  ├── weather_codes.py - WMO weather code to description mapping
  └── formatting.py - Temperature unit conversion, formatting helpers

app.py            - WeatherApp (main Textual App)
  - Orchestrates data fetching, widget updates, tab navigation, keyboard bindings
  - Manages app state (_weather_data, _location, _units)
  - Uses @work decorator for async fetching (keeps UI responsive)
  - Auto-refreshes every 30 minutes

__main__.py       - CLI entry point with argparse
  - Accepts --city, --location (lat,lon), --units (metric/imperial)
  - Manages config file at ~/.config/weather-cmd/config.json
  - Passes resolved location and units to WeatherApp
```

### Data Flow

1. **User launches app** → CLI parses args/config → Resolves location (city → coordinates via geocoding)
2. **WeatherApp.on_mount** → Spawns async worker to fetch_weather
3. **fetch_weather** → Calls API clients in parallel (open-meteo, NOAA alerts, RainViewer radar)
4. **API clients** → Parse JSON responses into typed dataclasses
5. **WeatherApp receives data** → Updates all widget views with new WeatherData
6. **Widgets render** using Textual's rendering engine

### Key Components

- **WeatherApp** (`app.py`): Central controller. Manages tabs (1-5 keybindings), refresh (r), quit (q). Also [ and ] for graph range cycling.
- **ForecastGraphs** (`widgets/graphs.py`): Complex widget with 6 plotext charts. Cycles through time ranges (12h, 24h, 48h, 72h, 168h). Uses conditional x-axis formatting (timestamps to hour labels).
- **OpenMeteoAPI** (`api/openmeteo.py`): Transforms JSON into dataclasses. Handles unit conversion (Celsius→Fahrenheit, m/s→mph, etc.).
- **Models** (`models.py`): Strict dataclass schemas ensure type safety across the app.

## Development

### Setup

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install in development mode with dev dependencies
pip install -e ".[dev]"
```

### Run the App

```bash
# Run with default config or no location
python -m weather_cmd

# Specify a city
python -m weather_cmd --city Denver

# Specify coordinates (lat,lon)
python -m weather_cmd --location "39.74,-104.98"

# Override units (default: imperial)
python -m weather_cmd --city Denver --units metric

# Save location to config
python -m weather_cmd --city Denver --save-location
```

### Run Tests

```bash
# Run all tests
pytest

# Run a specific test file
pytest tests/test_api_parsing.py

# Run a specific test
pytest tests/test_api_parsing.py::test_geocode_city

# Run with verbose output
pytest -v

# Run with asyncio debug output
pytest -v -s
```

Tests use **respx** to mock HTTP responses, so they don't require actual API calls. Located in `tests/`.

### Build and Install

```bash
# Build distribution
python -m pip install hatchling
python -m hatchling build

# Install from wheel
pip install dist/weather_cmd-*.whl
```

## Known Issues & Improvements (from CODE-ANALYSIS-GEM.md)

1. **HTTP Client Pooling**: `fetch_weather` creates a new `httpx.AsyncClient` per call. Should reuse a persistent client in `on_mount`/`on_unmount` for connection pooling and keep-alive.

2. **Error Swallowing**: Bare `except Exception: pass` in `fetch_weather` (radar) and range actions hides errors. Add logging to surface failures.

3. **Graph Rendering**: `ForecastGraphs.update_data` does `plt.clf()` then replot all 6 graphs on every range change. Could cause flicker on slow terminals. Consider incremental updates.

4. **Test Coverage**: Only API parsing tested. Missing:
   - UI logic (tab switching, data binding)
   - Graph range cycling
   - Widget updates on data changes
   - Edge cases (malformed config, timeouts)

5. **Code Repetition**: `_draw_*` methods in `graphs.py` are boilerplate. Could be refactored to a single `_draw_series(plot_id, x, y, label, color, unit)` helper.

## Important Patterns & Conventions

- **Async**: All I/O is async (httpx.AsyncClient, @work decorator in Textual). Use `async def` and `await` consistently.
- **Type Hints**: Modern Python type syntax (`list[float]`, `str | None`). Always annotate function signatures.
- **Dataclasses**: Use `@dataclass` for data models, not dicts.
- **Unit Conversion**: Conversion logic is in `OpenMeteoAPI.fetch_forecast()` and `utils/formatting.py`. Always apply unit conversion when passing data to widgets if needed.
- **Config**: Stored as JSON in `~/.config/weather-cmd/config.json`. Load/save via `__main__.py` utilities.
- **Textual Bindings**: Actions are defined in `BINDINGS` list, implemented as `action_*` methods.

## Testing Notes

- Use `respx.mock` decorator and context manager to mock HTTP responses.
- Use `pytest.mark.asyncio` for async test functions.
- Tests import from `weather_cmd` package (src layout), so install with `pip install -e ".[dev]"` first.
- No fixtures for widgets (TUI testing is complex). API parsing tests are most valuable.

## Configuration

Config file: `~/.config/weather-cmd/config.json`

Example:
```json
{
  "city": "Denver",
  "units": "imperial"
}
```

Or by coordinates:
```json
{
  "latitude": 39.74,
  "longitude": -104.99,
  "units": "imperial"
}
```

## Debugging Tips

1. Check `.textual.log` for Textual-specific logs (auto-generated).
2. Add `print()` statements before `app.run()` in `__main__.py` to verify CLI args/config.
3. Mock API responses with respx if adding new API calls.
4. Use `pytest -v -s` to see print output during test runs.

## References

- [Textual Docs](https://textual.textualize.io/)
- [Open-Meteo API](https://open-meteo.com/en/docs)
- [NOAA Alerts API](https://api.weather.gov/)
- [plotext Docs](https://github.com/piccolomo/plotext)
