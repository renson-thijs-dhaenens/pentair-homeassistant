"""Switch platform for Pentair Water Softener."""
from __future__ import annotations

import logging
from typing import Any

import requests

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
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
        PentairWaterHolidayModeSwitch(coordinator, entry, api),
    ]

    async_add_entities(entities)


class PentairWaterHolidayModeSwitch(PentairWaterEntity, SwitchEntity):
    """Representation of Pentair Water Softener holiday mode switch."""

    _attr_translation_key = "holiday_mode"


    def __init__(self, coordinator, entry: PentairWaterConfigEntry, api) -> None:
        """Initialize the holiday mode switch."""
        super().__init__(coordinator, entry)
        self._api = api
        self._attr_unique_id = f"{self._device_id}_holiday_mode"

    @property
    def is_on(self) -> bool | None:
        """Return true if holiday mode is on."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("holiday_mode", False)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on holiday mode."""
        _LOGGER.debug("Turning on holiday mode")
        try:
            await self.hass.async_add_executor_job(self._set_holiday_mode, True)
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Error turning on holiday mode: %s", err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off holiday mode."""
        _LOGGER.debug("Turning off holiday mode")
        try:
            await self.hass.async_add_executor_job(self._set_holiday_mode, False)
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Error turning off holiday mode: %s", err)

    def _set_holiday_mode(self, state: bool) -> None:
        """Set holiday mode via API."""
        self._api._setup_if_needed()
        device_id = self._api.device.id

        # Use the holiday endpoint
        url = f"{self._api._base_url}/{self._api._api}/water_softeners/{device_id}/holiday"
        headers = {
            'User-Agent': 'App/3.5.1 (iPhone; iOS 15.1.1; Scale/2.0.0)',
            'app_version': '3.5.1',
            'language': 'en',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        headers.update(self._api._auth_headers())

        # Toggle holiday mode
        data = {"holiday_mode": state}

        response = requests.post(url, json=data, headers=headers, verify=False)
        _LOGGER.debug("Holiday mode API response: %s - %s", response.status_code, response.text)

        if response.status_code not in (200, 201, 204):
            _LOGGER.warning("Holiday mode request returned status %s", response.status_code)
