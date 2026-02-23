"""CLI entry point for weather-cmd."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "weather-cmd"
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_config() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def save_config(config: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="weather-cmd",
        description="Terminal weather app with forecast graphs",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--city", type=str, help="City name (e.g. 'Denver')")
    group.add_argument("--zipcode", type=str, help="Zip/postal code (e.g. '80202')")
    group.add_argument(
        "--location",
        type=str,
        help="Latitude,Longitude (e.g. '39.74,-104.98')",
    )
    parser.add_argument(
        "--units",
        choices=["metric", "imperial"],
        default=None,
        help="Unit system (default: imperial)",
    )
    parser.add_argument(
        "--save-location",
        action="store_true",
        help="Save the resolved location to config",
    )

    args = parser.parse_args()

    config = load_config()
    city: str | None = args.city
    zipcode: str | None = args.zipcode
    coords: tuple[float, float] | None = None
    units: str = args.units or config.get("units", "imperial")

    if args.location:
        try:
            parts = args.location.split(",")
            coords = (float(parts[0].strip()), float(parts[1].strip()))
        except (ValueError, IndexError):
            print("Error: --location must be LAT,LON (e.g. '39.74,-104.98')", file=sys.stderr)
            sys.exit(1)
    elif not zipcode:
        city = config.get("city")
        zipcode = config.get("zipcode")
        if not city and not zipcode and "latitude" in config and "longitude" in config:
            coords = (config["latitude"], config["longitude"])

    if args.save_location:
        if city:
            config["city"] = city
            config.pop("zipcode", None)
            config.pop("latitude", None)
            config.pop("longitude", None)
        elif zipcode:
            config["zipcode"] = zipcode
            config.pop("city", None)
            config.pop("latitude", None)
            config.pop("longitude", None)
        elif coords:
            config["latitude"] = coords[0]
            config["longitude"] = coords[1]
            config.pop("city", None)
            config.pop("zipcode", None)
        if args.units:
            config["units"] = units
        save_config(config)

    if args.units:
        config["units"] = units
        save_config(config)

    from weather_cmd.app import WeatherApp

    app = WeatherApp(city=city, coords=coords, zipcode=zipcode, units=units)
    app.run()


if __name__ == "__main__":
    main()
