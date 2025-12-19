"""Pentair Water Softener integration for Home Assistant."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from erie_connect.client import ErieConnect

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_ACCESS_TOKEN,
    CONF_CLIENT_ID,
    CONF_DEVICE_ID,
    CONF_DEVICE_NAME,
    CONF_EMAIL,
    CONF_EXPIRY,
    CONF_PASSWORD,
    CONF_UID,
    DATA_API,
    DATA_COORDINATOR,
    DOMAIN,
    SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]

type PentairWaterConfigEntry = ConfigEntry[PentairWaterData]


class PentairWaterData:
    """Data class to hold API and coordinator."""

    def __init__(self, api: ErieConnect, coordinator: DataUpdateCoordinator) -> None:
        """Initialize the data class."""
        self.api = api
        self.coordinator = coordinator


async def async_setup_entry(hass: HomeAssistant, entry: PentairWaterConfigEntry) -> bool:
    """Set up Pentair Water Softener from a config entry."""
    _LOGGER.debug("Setting up Pentair Water Softener integration")

    # Create API client with stored credentials
    api = ErieConnect(
        entry.data[CONF_EMAIL],
        entry.data[CONF_PASSWORD],
        ErieConnect.Auth(
            entry.data[CONF_ACCESS_TOKEN],
            entry.data[CONF_CLIENT_ID],
            entry.data[CONF_UID],
            entry.data[CONF_EXPIRY],
        ),
        ErieConnect.Device(
            entry.data[CONF_DEVICE_ID],
            entry.data[CONF_DEVICE_NAME],
        ),
    )

    async def async_update_data() -> dict[str, Any]:
        """Fetch data from API endpoint."""
        try:
            response = await hass.async_add_executor_job(api.info)
            response_dashboard = await hass.async_add_executor_job(api.dashboard)

            # Parse total volume - remove unit suffix if present
            total_volume_raw = response.content.get("total_volume", "0")
            if isinstance(total_volume_raw, str):
                total_volume = total_volume_raw.split()[0]
            else:
                total_volume = str(total_volume_raw)

            return {
                "last_regeneration": response.content.get("last_regeneration"),
                "nr_regenerations": response.content.get("nr_regenerations"),
                "last_maintenance": response.content.get("last_maintenance"),
                "total_volume": total_volume,
                "warnings": response_dashboard.content.get("warnings", []),
                "serial": response.content.get("serial"),
                "software": response.content.get("software", "").strip(),
                "status": response_dashboard.content.get("status", {}),
            }
        except Exception as err:
            _LOGGER.error("Error fetching Pentair data: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store data in runtime_data
    entry.runtime_data = PentairWaterData(api, coordinator)

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: PentairWaterConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
