# weather-cmd

Terminal weather app with forecast graphs, radar, alerts, and ZIP/city/location lookup.

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
