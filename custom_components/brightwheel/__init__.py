"""The Brightwheel integration.

Modified 2026 by sNNNeaker: email/2FA login, new entities.
"""

from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import BrightwheelApi
from .const import CONF_COOKIE, CONF_CSRF, CONF_GUARDIAN_ID, CONF_TOKEN
from .coordinator import BrightwheelConfigEntry, BrightwheelCoordinator

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.EVENT,
    Platform.IMAGE,
    Platform.SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: BrightwheelConfigEntry) -> bool:
    """Set up Brightwheel from a config entry."""
    api = BrightwheelApi(
        async_create_clientsession(hass),
        token=entry.data.get(CONF_TOKEN),
        cookie=entry.data.get(CONF_COOKIE),
        csrf=entry.data.get(CONF_CSRF),
        guardian_id=entry.data.get(CONF_GUARDIAN_ID),
    )
    coordinator = BrightwheelCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: BrightwheelConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
