"""Event platform for Brightwheel.

Added 2026 by sNNNeaker.
"""

from __future__ import annotations

from homeassistant.components.event import EventEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import BrightwheelConfigEntry, BrightwheelCoordinator
from .data import (
    EVENT_TYPES,
    activity_time,
    actor_name,
    event_type,
    image_url,
)
from .entity import BrightwheelEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BrightwheelConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up event entities."""
    coordinator = entry.runtime_data
    async_add_entities(
        BrightwheelActivityEvent(coordinator, student_id)
        for student_id in coordinator.data
    )


class BrightwheelActivityEvent(BrightwheelEntity, EventEntity):
    """Fires for every new activity."""

    _attr_event_types = EVENT_TYPES

    def __init__(self, coordinator: BrightwheelCoordinator, student_id: str) -> None:
        """Initialize and seed the seen set with existing history."""
        super().__init__(coordinator, student_id, "activity")
        student = self.student
        self._seen: set[str] = {
            str(a["object_id"])
            for a in (student.activities if student else [])
            if a.get("object_id")
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Trigger events for unseen activities, oldest first."""
        student = self.student
        if student is not None:
            new = [
                a
                for a in student.activities
                if a.get("object_id") and str(a["object_id"]) not in self._seen
            ]
            for activity in reversed(new):  # activities are newest first
                self._seen.add(str(activity["object_id"]))
                when = activity_time(activity)
                self._trigger_event(
                    event_type(activity),
                    {
                        "time": when.isoformat() if when else None,
                        "note": activity.get("note"),
                        "by": actor_name(activity),
                        "image_url": image_url(activity),
                    },
                )
        self.async_write_ha_state()
