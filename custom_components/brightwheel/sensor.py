"""Sensor platform for Brightwheel.

Added 2026 by sNNNeaker.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .coordinator import BrightwheelConfigEntry, BrightwheelCoordinator
from .data import (
    activity_time,
    actor_name,
    friendly_type,
    last_check,
    today_activities,
)
from .entity import BrightwheelEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BrightwheelConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors."""
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = []
    for student_id in coordinator.data:
        entities.append(BrightwheelLastCheckSensor(coordinator, student_id, True))
        entities.append(BrightwheelLastCheckSensor(coordinator, student_id, False))
        entities.append(BrightwheelLatestActivitySensor(coordinator, student_id))
    async_add_entities(entities)


class BrightwheelLastCheckSensor(BrightwheelEntity, SensorEntity):
    """Time of the last check-in or check-out."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(
        self, coordinator: BrightwheelCoordinator, student_id: str, check_in: bool
    ) -> None:
        """Initialize."""
        super().__init__(
            coordinator, student_id, "last_check_in" if check_in else "last_check_out"
        )
        self._check_in = check_in

    @property
    def native_value(self) -> datetime | None:
        """Return the time."""
        student = self.student
        return last_check(student.activities, self._check_in)[0] if student else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return who did it."""
        student = self.student
        by = last_check(student.activities, self._check_in)[1] if student else None
        return {"by": by}


class BrightwheelLatestActivitySensor(BrightwheelEntity, SensorEntity):
    """The most recent activity."""

    def __init__(self, coordinator: BrightwheelCoordinator, student_id: str) -> None:
        """Initialize."""
        super().__init__(coordinator, student_id, "latest_activity")

    @property
    def native_value(self) -> str | None:
        """Return the friendly type of the newest activity."""
        student = self.student
        if not student or not student.activities:
            return None
        return friendly_type(student.activities[0])[:255]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return details and today's list."""
        student = self.student
        if not student:
            return {}
        today = today_activities(student.activities, dt_util.now())
        if not student.activities:
            return {"today": today}
        newest = student.activities[0]
        when = activity_time(newest)
        return {
            "time": when.isoformat() if when else None,
            "note": newest.get("note"),
            "by": actor_name(newest),
            "today": today,
        }
