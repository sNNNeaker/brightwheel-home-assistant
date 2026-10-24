"""Base entity for Brightwheel.

Added 2026 by sNNNeaker.
"""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BrightwheelCoordinator
from .data import StudentData


class BrightwheelEntity(CoordinatorEntity[BrightwheelCoordinator]):
    """Base class for per-student Brightwheel entities."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: BrightwheelCoordinator, student_id: str, key: str
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.student_id = student_id
        self._attr_translation_key = key
        self._attr_unique_id = f"{student_id}_{key}"
        student = (coordinator.data or {}).get(student_id)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, student_id)},
            name=student.name if student else student_id,
            manufacturer="Brightwheel",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def student(self) -> StudentData | None:
        """Return the current data of this student."""
        return (self.coordinator.data or {}).get(self.student_id)

    @property
    def available(self) -> bool:
        """Entity is available while the student data exists."""
        return super().available and self.student is not None
