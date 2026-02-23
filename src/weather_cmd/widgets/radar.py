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

from PIL import Image


class RadarView(Widget):
    def compose(self) -> ComposeResult:
        yield Label("Radar", id="radar-title")
        yield Static("Loading radar data...", id="radar-content")

    def update_data(self, image_data: bytes | None) -> None:
        content_container = self.query_one("#radar-content", Static)

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
                img_widget = TextualImage(img, id="radar-image")
                self.mount(img_widget)
            except Exception:
                self.mount(Static("Failed to render radar image.", id="radar-content"))
        else:
            content_container.update("Install textual-image for radar display.\npip install textual-image")
