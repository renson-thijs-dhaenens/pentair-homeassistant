"""Binary sensor platform for Pentair Water Softener."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import PentairWaterConfigEntry
from .const import ATTR_WARNINGS
from .entity import PentairWaterEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PentairWaterConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pentair Water Softener binary sensors."""
    coordinator = entry.runtime_data.coordinator

    async_add_entities([PentairWaterLowSaltSensor(coordinator, entry)])


class PentairWaterLowSaltSensor(PentairWaterEntity, BinarySensorEntity):
    """Binary sensor for low salt warning."""

    _attr_translation_key = "low_salt"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator, entry: PentairWaterConfigEntry) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._device_id}_low_salt"

    @property
    def is_on(self) -> bool:
        """Return true if low salt warning is active."""
        if self.coordinator.data is None:
            return False

        warnings = self.coordinator.data.get(ATTR_WARNINGS, [])
        if not warnings:
            return False

        # Check if any warning contains "Salt" in the description
        for warning in warnings:
            description = warning.get("description", "")
            if "Salt" in description or "salt" in description.lower():
                return True

        return False

