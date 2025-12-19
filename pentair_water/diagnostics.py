"""Diagnostics support for Pentair Water Softener."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_DEVICE_ID, CONF_DEVICE_NAME, CONF_EMAIL

TO_REDACT = {"email", "password", "access_token", "client_id", "uid"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data.coordinator

    # Redact sensitive information
    config_data = {
        key: "**REDACTED**" if key in TO_REDACT else value
        for key, value in entry.data.items()
    }

    return {
        "config_entry": config_data,
        "coordinator_data": coordinator.data,
    }
