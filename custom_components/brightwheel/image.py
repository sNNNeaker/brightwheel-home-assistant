"""Image platform for Brightwheel.

Added 2026 by sNNNeaker.
"""

from __future__ import annotations

from homeassistant.components.image import ImageEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import BrightwheelConfigEntry, BrightwheelCoordinator
from .data import latest_photo
from .entity import BrightwheelEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BrightwheelConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up image entities."""
    coordinator = entry.runtime_data
    async_add_entities(
        BrightwheelLatestPhoto(coordinator, student_id)
        for student_id in coordinator.data
    )


class BrightwheelLatestPhoto(BrightwheelEntity, ImageEntity):
    """The newest photo of the child."""

    def __init__(self, coordinator: BrightwheelCoordinator, student_id: str) -> None:
        """Initialize."""
        BrightwheelEntity.__init__(self, coordinator, student_id, "latest_photo")
        ImageEntity.__init__(self, coordinator.hass)
        self._update_image()

    def _update_image(self) -> None:
        student = self.student
        url, when = latest_photo(student.activities) if student else (None, None)
        self._attr_image_url = url
        self._attr_image_last_updated = when

    @callback
    def _handle_coordinator_update(self) -> None:
        """Refresh the photo, then write state."""
        self._update_image()
        super()._handle_coordinator_update()
