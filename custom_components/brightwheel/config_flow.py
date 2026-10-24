"""Config flow for Brightwheel integration.

Modified 2026 by sNNNeaker: email/2FA login, new entities.
"""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import SOURCE_REAUTH, ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import (
    BrightwheelApi,
    BrightwheelAuthError,
    BrightwheelConnectionError,
    BrightwheelError,
)
from .const import (
    CONF_CODE,
    CONF_COOKIE,
    CONF_CSRF,
    CONF_EMAIL,
    CONF_GUARDIAN_ID,
    CONF_PASSWORD,
    CONF_TOKEN,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

PASSWORD_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))


class BrightwheelConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Brightwheel (email, password, emailed code)."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize; credentials live only in memory during the flow."""
        self._email: str = ""
        self._password: str = ""
        self._api: BrightwheelApi | None = None
        self._two_factor_required = False

    async def _async_start(self) -> str | None:
        """Start login. Return an error key or None."""
        self._api = BrightwheelApi(async_create_clientsession(self.hass))
        try:
            self._two_factor_required = await self._api.async_start_login(
                self._email, self._password
            )
        except BrightwheelAuthError:
            return "invalid_auth"
        except BrightwheelConnectionError:
            return "cannot_connect"
        except BrightwheelError:
            return "unknown"
        return None

    async def _async_next_after_start(self) -> ConfigFlowResult:
        if self._two_factor_required:
            return await self.async_step_two_factor()
        return await self._async_finish(None)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for email and password."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._email = user_input[CONF_EMAIL].strip()
            self._password = user_input[CONF_PASSWORD]
            if error := await self._async_start():
                errors["base"] = error
            else:
                return await self._async_next_after_start()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EMAIL, default=self._email): str,
                    vol.Required(CONF_PASSWORD): PASSWORD_SELECTOR,
                }
            ),
            errors=errors,
        )

    async def async_step_two_factor(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the emailed code."""
        errors: dict[str, str] = {}
        if user_input is not None:
            result = await self._async_finish(user_input[CONF_CODE].strip(), errors)
            if result is not None:
                return result
        return self.async_show_form(
            step_id="two_factor",
            data_schema=vol.Schema({vol.Required(CONF_CODE): str}),
            errors=errors,
        )

    async def _async_finish(
        self, code: str | None, errors: dict[str, str] | None = None
    ) -> ConfigFlowResult | None:
        """Finish login, load students and create or update the entry.

        Without an errors dict (no 2FA), failures re-show the matching form.
        """
        local_errors = errors if errors is not None else {}
        assert self._api is not None
        try:
            creds = await self._api.async_finish_login(
                self._email, self._password, code
            )
            students = await self._api.async_get_students()
            if students and not creds.get("guardian_id"):
                creds["guardian_id"] = await self._api.async_get_guardian_id()
        except BrightwheelAuthError:
            local_errors["base"] = "invalid_code" if code else "invalid_auth"
        except BrightwheelConnectionError:
            local_errors["base"] = "cannot_connect"
        except BrightwheelError:
            local_errors["base"] = "unknown"
        else:
            if not students:
                local_errors["base"] = "no_students"
        if local_errors:
            if errors is not None:
                return None
            return self.async_show_form(
                step_id="reauth_confirm" if self.source == SOURCE_REAUTH else "user",
                data_schema=self._password_schema(),
                description_placeholders={"email": self._email},
                errors=local_errors,
            )

        data = {
            CONF_EMAIL: self._email,
            CONF_TOKEN: creds["token"],
            CONF_COOKIE: creds["cookie"],
            CONF_CSRF: creds["csrf"],
            CONF_GUARDIAN_ID: creds["guardian_id"],
        }
        self._password = ""
        await self.async_set_unique_id(creds["guardian_id"])
        if self.source == SOURCE_REAUTH:
            self._abort_if_unique_id_mismatch(reason="wrong_account")
            return self.async_update_reload_and_abort(
                self._get_reauth_entry(), data_updates=data
            )
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title=self._email, data=data)

    def _password_schema(self) -> vol.Schema:
        if self.source == SOURCE_REAUTH:
            return vol.Schema({vol.Required(CONF_PASSWORD): PASSWORD_SELECTOR})
        return vol.Schema(
            {
                vol.Required(CONF_EMAIL, default=self._email): str,
                vol.Required(CONF_PASSWORD): PASSWORD_SELECTOR,
            }
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Start reauthentication."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the password again."""
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        self._email = entry.data[CONF_EMAIL]
        if user_input is not None:
            self._password = user_input[CONF_PASSWORD]
            if error := await self._async_start():
                errors["base"] = error
            else:
                return await self._async_next_after_start()
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): PASSWORD_SELECTOR}),
            description_placeholders={"email": self._email},
            errors=errors,
        )
