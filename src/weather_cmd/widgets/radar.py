"""Radar image display widget."""

from __future__ import annotations

import io

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label, Static

try:
    from textual_image.widget import Image as TextualImage

    HAS_IMAGE = True
except ImportError:
    HAS_IMAGE = False

from PIL import Image, ImageDraw, ImageFont

from weather_cmd.models import Location


class RadarView(Widget):
    def compose(self) -> ComposeResult:
        yield Label("Radar", id="radar-title")
        yield Static("Loading radar...", id="radar-placeholder")

    def update_data(self, image_data: bytes | None, location: Location | None = None) -> None:
        # Remove any existing image or placeholder
        for widget_id in ("#radar-image", "#radar-placeholder", "#radar-content"):
            try:
                self.query_one(widget_id).remove()
            except Exception:
                pass

        if image_data is None:
            self.mount(Static("Radar data unavailable.", id="radar-placeholder"))
            return

        if HAS_IMAGE:
            try:
                img = Image.open(io.BytesIO(image_data))
                if location:
                    img = self._add_location_marker(img, location)
                self.mount(TextualImage(img, id="radar-image"))
            except Exception:
                self.mount(Static("Failed to render radar image.", id="radar-placeholder"))
        else:
            self.mount(Static(
                "Install textual-image for radar display.\npip install textual-image",
                id="radar-placeholder",
            ))

    def _add_location_marker(self, img: Image.Image, location: Location) -> Image.Image:
        """Add a crosshair location marker at the image center."""
        try:
            img_copy = img.copy().convert("RGBA")
            draw = ImageDraw.Draw(img_copy)

            width, height = img_copy.size
            cx, cy = width // 2, height // 2
            sz = 30  # crosshair arm length

            # Black outline for contrast
            draw.line([(cx - sz, cy), (cx + sz, cy)], fill=(0, 0, 0, 255), width=4)
            draw.line([(cx, cy - sz), (cx, cy + sz)], fill=(0, 0, 0, 255), width=4)

            # White crosshair
            draw.line([(cx - sz, cy), (cx + sz, cy)], fill=(255, 255, 255, 255), width=2)
            draw.line([(cx, cy - sz), (cx, cy + sz)], fill=(255, 255, 255, 255), width=2)

            # Red center dot with black outline
            dot = 5
            draw.ellipse([(cx - dot - 1, cy - dot - 1), (cx + dot + 1, cy + dot + 1)], fill=(0, 0, 0, 255))
            draw.ellipse([(cx - dot, cy - dot), (cx + dot, cy + dot)], fill=(220, 50, 50, 255))

            # City label with dark background
            try:
                font = ImageFont.load_default()
            except Exception:
                font = None
            text = location.name
            tx, ty = cx + sz + 6, cy - 8
            # Approximate background box (default font is 8px tall, ~6px per char wide)
            box_w = len(text) * 6 + 4
            draw.rectangle([tx - 2, ty - 2, tx + box_w, ty + 12], fill=(0, 0, 0, 180))
            draw.text((tx, ty), text, fill=(255, 255, 255, 255), font=font)

            return img_copy
        except Exception:
            return img
