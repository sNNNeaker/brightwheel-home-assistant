"""Binary sensor platform for Brightwheel.

Added 2026 by sNNNeaker.
"""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .coordinator import BrightwheelConfigEntry, BrightwheelCoordinator
from .data import is_checked_in_today
from .entity import BrightwheelEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BrightwheelConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        BrightwheelCheckedInSensor(coordinator, student_id)
        for student_id in coordinator.data
    )


class BrightwheelCheckedInSensor(BrightwheelEntity, BinarySensorEntity):
    """Whether the child is checked in today."""

    _attr_icon = "mdi:account-check"

    def __init__(self, coordinator: BrightwheelCoordinator, student_id: str) -> None:
        """Initialize."""
        super().__init__(coordinator, student_id, "checked_in")

    @property
    def is_on(self) -> bool | None:
        """Return True if checked in."""
        student = self.student
        if student is None:
            return None
        return is_checked_in_today(student.activities, dt_util.now())
