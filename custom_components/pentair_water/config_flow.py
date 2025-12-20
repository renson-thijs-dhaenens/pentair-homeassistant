"""Config flow for Pentair Water Softener integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from erie_connect.client import ErieConnect

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector

from .const import (
    CONF_ACCESS_TOKEN,
    CONF_CLIENT_ID,
    CONF_DEVICE_ID,
    CONF_DEVICE_NAME,
    CONF_EMAIL,
    CONF_EXPIRY,
    CONF_FLOW_SCAN_INTERVAL,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_UID,
    DEFAULT_FLOW_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


def _login_and_select_first_active_device(api: ErieConnect) -> str:
    """Login to Erie Connect and select first active device."""
    _LOGGER.debug("Logging in to Erie Connect")
    api.login()

    _LOGGER.debug("Selecting first active device")
    api.select_first_active_device()

    if api.device is None or api.auth is None:
        raise InvalidAuth("No device found or authentication failed")

    return api.device.id


class PentairWaterConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Pentair Water Softener."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return PentairWaterOptionsFlowHandler()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            email = user_input[CONF_EMAIL]
            password = user_input[CONF_PASSWORD]

            api = ErieConnect(email, password)

            try:
                device_id = await self.hass.async_add_executor_job(
                    _login_and_select_first_active_device, api
                )
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception during login")
                errors["base"] = "unknown"
            else:
                # Check if already configured
                await self.async_set_unique_id(device_id)
                self._abort_if_unique_id_configured()

                # Create config entry with all required data
                return self.async_create_entry(
                    title=api.device.name or "Pentair Water Softener",
                    data={
                        CONF_EMAIL: email,
                        CONF_PASSWORD: password,
                        CONF_ACCESS_TOKEN: api.auth.access_token,
                        CONF_CLIENT_ID: api.auth.client,
                        CONF_UID: api.auth.uid,
                        CONF_EXPIRY: api.auth.expiry,
                        CONF_DEVICE_ID: api.device.id,
                        CONF_DEVICE_NAME: api.device.name,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class PentairWaterOptionsFlowHandler(OptionsFlow):
    """Handle options flow for Pentair Water Softener."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        current_flow_interval = self.config_entry.options.get(
            CONF_FLOW_SCAN_INTERVAL, DEFAULT_FLOW_SCAN_INTERVAL
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=current_interval,
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=30,
                            max=3600,
                            step=30,
                            unit_of_measurement="seconds",
                            mode=selector.NumberSelectorMode.SLIDER,
                        ),
                    ),
                    vol.Optional(
                        CONF_FLOW_SCAN_INTERVAL,
                        default=current_flow_interval,
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1,
                            max=60,
                            step=1,
                            unit_of_measurement="seconds",
                            mode=selector.NumberSelectorMode.SLIDER,
                        ),
                    ),
                }
            ),
        )
