"""Button platform for Pentair Water Softener."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
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
    """Set up Pentair Water Softener buttons."""
    coordinator = entry.runtime_data.coordinator
    api = entry.runtime_data.api

    entities: list[ButtonEntity] = [
        PentairWaterForceRegenerationButton(coordinator, entry, api),
    ]

    async_add_entities(entities)


class PentairWaterForceRegenerationButton(PentairWaterEntity, ButtonEntity):
    """Button to force regeneration on the water softener."""

    _attr_translation_key = "force_regeneration"


    def __init__(self, coordinator, entry: PentairWaterConfigEntry, api) -> None:
        """Initialize the button."""
        super().__init__(coordinator, entry)
        self._api = api
        self._attr_unique_id = f"{self._device_id}_force_regeneration"

    async def async_press(self) -> None:
        """Handle the button press - trigger regeneration."""
        _LOGGER.info("Triggering manual regeneration for Pentair water softener")
        try:
            await self.hass.async_add_executor_job(self._trigger_regeneration)
            # Refresh data after triggering
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Error triggering regeneration: %s", err)

    def _trigger_regeneration(self) -> None:
        """Trigger regeneration via API."""
        import requests

        self._api._setup_if_needed()
        device_id = self._api.device.id

        # Try the regeneration endpoint
        url = f"{self._api._base_url}/{self._api._api}/water_softeners/{device_id}/regeneration"
        headers = {
            'User-Agent': 'App/3.5.1 (iPhone; iOS 15.1.1; Scale/2.0.0)',
            'app_version': '3.5.1',
            'language': 'en',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        headers.update(self._api._auth_headers())

        response = requests.post(url, headers=headers, verify=False)
        _LOGGER.debug("Regeneration API response: %s - %s", response.status_code, response.text)

        if response.status_code not in (200, 201, 204):
            _LOGGER.warning("Regeneration request returned status %s", response.status_code)
