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
        yield Static("Loading radar data...", id="radar-content")
        yield Label("Location:", id="location-label")
        yield Static("", id="location-info")
        yield Label("Nearby Cities:", id="nearby-label")
        yield Static("", id="nearby-cities")

    def update_data(self, image_data: bytes | None, location: Location | None = None) -> None:
        content_container = self.query_one("#radar-content", Static)

        # Update location info
        if location:
            self.query_one("#location-info", Static).update(
                f"{location.display_name} ({location.latitude:.2f}, {location.longitude:.2f})"
            )
        else:
            self.query_one("#location-info", Static).update("Location data unavailable")

        # Update nearby cities (placeholder for now)
        if location:
            self.query_one("#nearby-cities", Static).update(
                f"Center: {location.name}\n(Nearby cities feature coming soon)"
            )
        else:
            self.query_one("#nearby-cities", Static).update("(No location data)")

        # Update radar image
        if image_data is None:
            content_container.update("Radar data unavailable.")
            return

        if HAS_IMAGE:
            try:
                content_container.remove()
            except Exception:
                pass
            try:
                img = Image.open(io.BytesIO(image_data))
                # Draw location marker on image if location data available
                if location:
                    img = self._add_location_to_image(img, location)
                img_widget = TextualImage(img, id="radar-image")
                self.mount(img_widget)
            except Exception:
                self.mount(Static("Failed to render radar image.", id="radar-content"))
        else:
            content_container.update("Install textual-image for radar display.\npip install textual-image")

    def _add_location_to_image(self, img: Image.Image, location: Location) -> Image.Image:
        """Add location marker to the radar image."""
        try:
            # Create a copy to avoid modifying original
            img_copy = img.copy()
            draw = ImageDraw.Draw(img_copy)

            # Calculate center point (assuming RainViewer images are centered on location)
            width, height = img_copy.size
            center_x, center_y = width // 2, height // 2

            # Draw a crosshair marker at the center
            marker_size = 20
            # Horizontal line
            draw.line(
                [(center_x - marker_size, center_y), (center_x + marker_size, center_y)],
                fill="white",
                width=2,
            )
            # Vertical line
            draw.line(
                [(center_x, center_y - marker_size), (center_x, center_y + marker_size)],
                fill="white",
                width=2,
            )
            # Center dot
            dot_size = 3
            draw.ellipse(
                [
                    (center_x - dot_size, center_y - dot_size),
                    (center_x + dot_size, center_y + dot_size),
                ],
                fill="red",
            )

            # Add text label with city name
            try:
                # Try to use a default font
                font = ImageFont.load_default()
            except Exception:
                font = None

            text = location.name
            # Place text above the marker
            text_y = center_y - marker_size - 20
            draw.text((center_x - 20, text_y), text, fill="white", font=font)

            return img_copy
        except Exception:
            # If drawing fails, return original image
            return img
