"""DataUpdateCoordinator for Brightwheel.

Modified 2026 by sNNNeaker: email/2FA login, new entities.
"""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import BrightwheelApi, BrightwheelAuthError, BrightwheelError
from .const import DOMAIN, HISTORY_DAYS, SCAN_INTERVAL
from .data import StudentData, sort_activities

_LOGGER = logging.getLogger(__name__)

type BrightwheelConfigEntry = ConfigEntry[BrightwheelCoordinator]


class BrightwheelCoordinator(DataUpdateCoordinator[dict[str, StudentData]]):
    """Fetch and cache Brightwheel activity data."""

    config_entry: BrightwheelConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: BrightwheelConfigEntry,
        api: BrightwheelApi,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=SCAN_INTERVAL,
        )
        self.api = api
        self._students: list[dict[str, Any]] = []
        self._school_names: dict[str, str | None] = {}

    async def _async_update_data(self) -> dict[str, StudentData]:
        """Fetch recent activities for every student."""
        try:
            if not self._students:
                self._students = await self.api.async_get_students()
                self._school_names.update(await self.api.async_get_school_names())
            end = dt_util.now().date() + timedelta(days=1)
            start = end - timedelta(days=HISTORY_DAYS + 1)
            result: dict[str, StudentData] = {}
            for student in self._students:
                student_id = str(student["object_id"])
                activities = await self.api.async_get_activities(student_id, start, end)
                name = (
                    f"{student.get('first_name') or ''} "
                    f"{student.get('last_name') or ''}"
                ).strip() or student_id
                school_id = student.get("school_id")
                if school_id and school_id not in self._school_names:
                    self._school_names[school_id] = (
                        await self.api.async_get_school_name(school_id)
                    )
                result[student_id] = StudentData(
                    student_id=student_id,
                    name=name,
                    activities=sort_activities(activities),
                    school_id=school_id,
                    school_name=self._school_names.get(school_id),
                    enrollment_status=student.get("enrollment_status"),
                )
        except BrightwheelAuthError as err:
            raise ConfigEntryAuthFailed("Brightwheel login expired") from err
        except BrightwheelError as err:
            raise UpdateFailed(f"Error communicating with Brightwheel: {err}") from err
        return result
