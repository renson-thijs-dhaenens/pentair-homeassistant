"""Binary sensor platform for Pentair Water Softener."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import PentairWaterConfigEntry
from .const import ATTR_WARNINGS, ATTR_LAST_MAINTENANCE
from .entity import PentairWaterEntity

_LOGGER = logging.getLogger(__name__)

# Default service interval is 2 years (730 days)
DEFAULT_SERVICE_INTERVAL_DAYS = 730


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PentairWaterConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pentair Water Softener binary sensors."""
    coordinator = entry.runtime_data.coordinator

    async_add_entities([
        PentairWaterLowSaltSensor(coordinator, entry),
        PentairWaterServiceDueSensor(coordinator, entry),
    ])


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


class PentairWaterServiceDueSensor(PentairWaterEntity, BinarySensorEntity):
    """Binary sensor for service/maintenance due."""

    _attr_translation_key = "service_due"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator, entry: PentairWaterConfigEntry) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._device_id}_service_due"

    @property
    def is_on(self) -> bool:
        """Return true if service/maintenance is due."""
        if self.coordinator.data is None:
            return False

        last_maintenance = self.coordinator.data.get(ATTR_LAST_MAINTENANCE)
        if not last_maintenance:
            return False

        try:
            # Parse the maintenance date
            if isinstance(last_maintenance, str):
                maintenance_date = datetime.fromisoformat(
                    last_maintenance.replace("Z", "+00:00")
                )
            else:
                maintenance_date = last_maintenance

            # Calculate next service date (1 year from last maintenance)
            next_service = maintenance_date + timedelta(days=DEFAULT_SERVICE_INTERVAL_DAYS)

            # Service is due if we're past the next service date or within 30 days
            days_until_service = (next_service - datetime.now(maintenance_date.tzinfo)).days
            return days_until_service <= 30

        except (ValueError, TypeError) as err:
            _LOGGER.debug("Error parsing maintenance date: %s", err)
            return False

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes."""
        if self.coordinator.data is None:
            return {}

        last_maintenance = self.coordinator.data.get(ATTR_LAST_MAINTENANCE)
        if not last_maintenance:
            return {}

        try:
            if isinstance(last_maintenance, str):
                maintenance_date = datetime.fromisoformat(
                    last_maintenance.replace("Z", "+00:00")
                )
            else:
                maintenance_date = last_maintenance

            next_service = maintenance_date + timedelta(days=DEFAULT_SERVICE_INTERVAL_DAYS)
            days_until = (next_service - datetime.now(maintenance_date.tzinfo)).days

            return {
                "last_maintenance": last_maintenance,
                "next_service_date": next_service.isoformat(),
                "days_until_service": days_until,
            }
        except (ValueError, TypeError):
            return {}

