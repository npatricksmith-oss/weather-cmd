"""RainViewer radar tile API client."""

from __future__ import annotations

import io
import math
import time

import httpx
from PIL import Image

RAINVIEWER_API = "https://api.rainviewer.com/public/weather-maps.json"
TILE_SIZE = 256
ZOOM = 6  # Good regional view


def _lat_lon_to_tile(lat: float, lon: float, zoom: int) -> tuple[int, int]:
    n = 2 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    lat_rad = math.radians(lat)
    y = int((1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
    return x, y


class RadarCache:
    def __init__(self) -> None:
        self._image: bytes | None = None
        self._fetched_at: float = 0
        self._ttl: float = 600  # 10 minutes

    @property
    def is_valid(self) -> bool:
        return self._image is not None and (time.monotonic() - self._fetched_at) < self._ttl

    @property
    def image(self) -> bytes | None:
        if self.is_valid:
            return self._image
        return None

    def store(self, img: bytes) -> None:
        self._image = img
        self._fetched_at = time.monotonic()


_cache = RadarCache()


async def fetch_radar(lat: float, lon: float, client: httpx.AsyncClient) -> bytes | None:
    cached = _cache.image
    if cached is not None:
        return cached

    try:
        resp = await client.get(RAINVIEWER_API, timeout=10.0)
        resp.raise_for_status()
        data = resp.json()
    except (httpx.HTTPError, httpx.TimeoutException):
        return None

    radar_frames = data.get("radar", {}).get("past", [])
    if not radar_frames:
        return None

    latest = radar_frames[-1]
    path = latest["path"]

    center_x, center_y = _lat_lon_to_tile(lat, lon, ZOOM)

    # Stitch 3x3 grid of tiles
    composite = Image.new("RGBA", (TILE_SIZE * 3, TILE_SIZE * 3))

    for dy in range(-1, 2):
        for dx in range(-1, 2):
            tx = center_x + dx
            ty = center_y + dy
            url = f"https://tilecache.rainviewer.com{path}/{TILE_SIZE}/{ZOOM}/{tx}/{ty}/2/1_1.png"
            try:
                tile_resp = await client.get(url, timeout=10.0)
                if tile_resp.status_code == 200:
                    tile_img = Image.open(io.BytesIO(tile_resp.content))
                    composite.paste(tile_img, ((dx + 1) * TILE_SIZE, (dy + 1) * TILE_SIZE))
            except (httpx.HTTPError, httpx.TimeoutException):
                continue

    buf = io.BytesIO()
    composite.save(buf, format="PNG")
    result = buf.getvalue()
    _cache.store(result)
    return result
