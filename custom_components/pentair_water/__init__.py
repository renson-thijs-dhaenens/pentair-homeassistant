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
    CONF_FLOW_SCAN_INTERVAL,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_UID,
    DATA_API,
    DATA_COORDINATOR,
    DEFAULT_FLOW_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.SWITCH, Platform.BUTTON]

type PentairWaterConfigEntry = ConfigEntry[PentairWaterData]


class PentairWaterData:
    """Data class to hold API and coordinator."""

    def __init__(self, api: ErieConnect, coordinator: DataUpdateCoordinator, flow_coordinator: DataUpdateCoordinator) -> None:
        """Initialize the data class."""
        self.api = api
        self.coordinator = coordinator
        self.flow_coordinator = flow_coordinator


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
            response_settings = await hass.async_add_executor_job(api.settings)
            response_flow = await hass.async_add_executor_job(api.flow)

            # Try to get features (may not be available on all devices)
            try:
                response_features = await hass.async_add_executor_job(api.features)
                features = response_features.content if response_features else {}
            except Exception:
                features = {}

            # Log raw API responses for debugging
            _LOGGER.debug("RAW API info: %s", response.content)
            _LOGGER.debug("RAW API dashboard: %s", response_dashboard.content)
            _LOGGER.debug("RAW API settings: %s", response_settings.content)
            _LOGGER.debug("RAW API flow: %s", response_flow.content)

            # Parse total volume - remove unit suffix if present
            total_volume_raw = response.content.get("total_volume", "0")
            if isinstance(total_volume_raw, str):
                total_volume = total_volume_raw.split()[0]
            else:
                total_volume = str(total_volume_raw)

            # Parse settings
            settings = response_settings.content if response_settings else {}
            settings_inner = settings.get("settings", {})

            # Parse flow data
            flow_data = response_flow.content if response_flow else {}

            # Parse dashboard data
            dashboard = response_dashboard.content if response_dashboard else {}

            # Log status specifically for debugging capacity_remaining
            status_data = dashboard.get("status", {})
            _LOGGER.debug("Dashboard status data: %s", status_data)

            return {
                "last_regeneration": response.content.get("last_regeneration"),
                "nr_regenerations": response.content.get("nr_regenerations"),
                "last_maintenance": response.content.get("last_maintenance"),
                "total_volume": total_volume,
                "warnings": dashboard.get("warnings", []),
                "serial": response.content.get("serial"),
                "software": response.content.get("software", "").strip(),
                "status": status_data,
                "settings": settings,
                "holiday_mode": dashboard.get("holiday_mode", False),
                "features": features,
                "flow": flow_data.get("flow", 0),
                "water_hardness": settings_inner.get("install_hardness"),
                "regen_time": dashboard.get("meta", {}).get("regen_time"),
            }
        except Exception as err:
            _LOGGER.error("Error fetching Pentair data: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    # Get scan interval from options, or use default
    scan_interval_seconds = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    update_interval = timedelta(seconds=scan_interval_seconds)
    
    flow_scan_interval_seconds = entry.options.get(CONF_FLOW_SCAN_INTERVAL, DEFAULT_FLOW_SCAN_INTERVAL)
    flow_update_interval = timedelta(seconds=flow_scan_interval_seconds)

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=update_interval,
    )

    # Create a separate coordinator for flow data that updates every 5 seconds
    async def async_update_flow_data() -> dict[str, Any]:
        """Fetch flow data from API endpoint."""
        try:
            response_flow = await hass.async_add_executor_job(api.flow)
            flow_data = response_flow.content if response_flow else {}
            _LOGGER.debug("RAW API flow (fast poll): %s", flow_data)
            return {
                "flow": flow_data.get("flow", 0),
            }
        except Exception as err:
            _LOGGER.error("Error fetching Pentair flow data: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    flow_coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}_flow",
        update_method=async_update_flow_data,
        update_interval=flow_update_interval,  # Configurable fast updates for flow
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    await flow_coordinator.async_config_entry_first_refresh()

    # Store data in runtime_data
    entry.runtime_data = PentairWaterData(api, coordinator, flow_coordinator)

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register options update listener
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_update_options(hass: HomeAssistant, entry: PentairWaterConfigEntry) -> None:
    """Handle options update - reload integration to apply new settings."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: PentairWaterConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
