# weather-cmd

Terminal weather app with forecast graphs, radar, alerts, and ZIP/city/location lookup.

## Requirements

- Python 3.12 or newer
- Internet access for forecast, alerts, geocoding, and radar data
- A terminal that can run Textual apps

No API key is required for the current providers.

## Python Dependencies

Runtime dependencies:

- `textual`
- `textual-plotext`
- `textual-image`
- `httpx`
- `pillow`

Development/test dependencies:

- `pytest`
- `pytest-asyncio`
- `respx`

These are installed automatically from `pyproject.toml`.

## Install

From a fresh clone:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

If you only want to run the app and do not need test tooling:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

You can also skip the manual setup and use the repo-local launcher:

```bash
./weather-cmd --city Boston
```

On first run it creates `.venv/`, installs the app, and then launches it.

## Run

After installation:

```bash
weather-cmd --city Boston
```

Other examples:

```bash
weather-cmd --zipcode 10001
weather-cmd --location 42.3601,-71.0589
weather-cmd --city Boston --units metric
weather-cmd --city Boston --save-location
```

If you do not want to activate the virtual environment, run the console script directly:

```bash
.venv/bin/weather-cmd --city Boston
```

From the repo root, this wrapper works too:

```bash
./weather-cmd --city Boston
```

## Verify The Install

Check the CLI wiring:

```bash
weather-cmd --help
```

Run tests:

```bash
pytest -q
```

## Troubleshooting

### `No module named weather_cmd`

The package has not been installed into your environment yet. Create a virtual environment and run:

```bash
pip install -e .
```

### `No module named httpx` or other missing package errors

The dependencies are not installed in the Python environment you are using. Activate the project virtual environment or use the binary inside `.venv/bin/`.

### `git pull` did not install anything

`git pull` only downloads committed files from the repository. It does not create `.venv/` or install Python packages. You must run the install commands above after pulling changes that affect dependencies or packaging.

### I want one command from the repo root

Use:

```bash
./weather-cmd --city Boston
```

That wrapper creates `.venv/` and installs the package automatically if needed.

## Status

Current forecast stack:

- Primary forecast provider: Open-Meteo
- US alerts / text forecast / county forecast: NOAA / `api.weather.gov`
- US forecast fallback when Open-Meteo is unavailable: NOAA / `api.weather.gov`

## Weather API Options To Consider

These are candidate providers to discuss later if we want a stronger or more flexible forecast stack.

### 1. met.no Locationforecast

Why consider it:

- Free, no API key required
- Global coverage
- Good fit as a secondary non-commercial-style fallback

Notes:

- Requires a proper custom `User-Agent`
- Good candidate for a global fallback when Open-Meteo is down

Docs:

- https://api.met.no/weatherapi/locationforecast/2.0/documentation

### 2. WeatherAPI

Why consider it:

- Simple JSON API
- Supports forecast plus geocoding/search use cases
- Good candidate for a commercial-friendly keyed backup

Notes:

- Free tier exists, but it adds API-key management and rate-limit considerations

Docs:

- https://www.weatherapi.com/docs
- https://www.weatherapi.com/pricing.aspx

### 3. Visual Crossing

Why consider it:

- Forecast, current, and historical weather in one service
- Reasonable fallback option if we want a broader feature set

Notes:

- Free usage exists, but request/record limits should be reviewed before adopting

Docs:

- https://www.visualcrossing.com/weather-api/

### 4. OpenWeather

Why consider it:

- Mature ecosystem
- Broad feature coverage
- Common choice if we want a mainstream keyed provider

Notes:

- Free usage exists, but pricing is call-based after the free allowance

Docs:

- https://openweathermap.org/price

### 5. Tomorrow.io

Why consider it:

- Modern API with strong feature coverage
- Worth considering if we want another commercial backup option

Notes:

- Free tier is more limited than some alternatives, so it is probably not the first backup to add

Docs:

- https://www.tomorrow.io/weather-api/

## Current Recommendation

If we revisit providers later, the strongest next options look like:

- Add `met.no` as a no-key global fallback
- Keep NOAA for US-specific coverage
- Consider `WeatherAPI` if we want a more stable keyed commercial backup
