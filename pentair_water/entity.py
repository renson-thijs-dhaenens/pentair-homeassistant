"""Base entity for Pentair Water Softener."""
from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import CONF_DEVICE_ID, CONF_DEVICE_NAME, DOMAIN, MANUFACTURER

if TYPE_CHECKING:
    from . import PentairWaterConfigEntry


class PentairWaterEntity(CoordinatorEntity):
    """Base class for Pentair Water Softener entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: PentairWaterConfigEntry,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._device_id = entry.data[CONF_DEVICE_ID]
        self._device_name = entry.data[CONF_DEVICE_NAME]

        # Get serial and software from coordinator data if available
        serial = None
        sw_version = None
        if coordinator.data:
            serial = coordinator.data.get("serial")
            sw_version = coordinator.data.get("software")

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=self._device_name or "Pentair Water Softener",
            manufacturer=MANUFACTURER,
            model="Water Softener",
            serial_number=serial,
            sw_version=sw_version,
        )
