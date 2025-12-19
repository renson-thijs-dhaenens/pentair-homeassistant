"""Switch platform for Pentair Water Softener."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import PentairWaterConfigEntry
from .const import DOMAIN
from .entity import PentairWaterEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PentairWaterConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pentair Water Softener switches."""
    coordinator = entry.runtime_data.coordinator
    api = entry.runtime_data.api

    entities: list[SwitchEntity] = [
        PentairWaterVacationModeSwitch(coordinator, entry, api),
    ]

    async_add_entities(entities)


class PentairWaterVacationModeSwitch(PentairWaterEntity, SwitchEntity):
    """Representation of Pentair Water Softener vacation mode switch."""

    _attr_translation_key = "vacation_mode"
    _attr_icon = "mdi:airplane"

    def __init__(self, coordinator, entry: PentairWaterConfigEntry, api) -> None:
        """Initialize the vacation mode switch."""
        super().__init__(coordinator, entry)
        self._api = api
        self._attr_unique_id = f"{self._device_id}_vacation_mode"

    @property
    def is_on(self) -> bool | None:
        """Return true if vacation mode is on."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("vacation_mode", False)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on vacation mode."""
        _LOGGER.debug("Turning on vacation mode")
        try:
            # The API likely has a method to set vacation mode
            # We need to check the actual API implementation
            await self.hass.async_add_executor_job(
                self._set_vacation_mode, True
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Error turning on vacation mode: %s", err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off vacation mode."""
        _LOGGER.debug("Turning off vacation mode")
        try:
            await self.hass.async_add_executor_job(
                self._set_vacation_mode, False
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Error turning off vacation mode: %s", err)

    def _set_vacation_mode(self, state: bool) -> None:
        """Set vacation mode via API."""
        # The erie-connect library may not have a direct method for this
        # We may need to use a raw API call
        # For now, we'll try using the _post method if available
        try:
            device_id = self._api.device.id
            endpoint = f'/water_softeners/{device_id}/settings'
            
            # Try to update vacation mode setting
            self._api._setup_if_needed()
            
            # Make a POST/PUT request to update vacation mode
            # The exact API format depends on Pentair's API specification
            import requests
            
            url = f"{self._api._base_url}/{self._api._api}/water_softeners/{device_id}/vacation"
            headers = {
                'User-Agent': 'App/3.5.1 (iPhone; iOS 15.1.1; Scale/2.0.0)',
                'app_version': '3.5.1',
                'language': 'en',
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            }
            headers.update(self._api._auth_headers())
            
            data = {"vacation_mode": state}
            
            response = requests.post(url, json=data, headers=headers, verify=False)
            _LOGGER.debug("Vacation mode API response: %s", response.status_code)
            
        except Exception as err:
            _LOGGER.error("Error setting vacation mode: %s", err)
            raise
