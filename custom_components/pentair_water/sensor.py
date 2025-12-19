"""Sensor platform for Pentair Water Softener."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfVolume
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import PentairWaterConfigEntry
from .const import (
    ATTR_LAST_MAINTENANCE,
    ATTR_LAST_REGENERATION,
    ATTR_NR_REGENERATIONS,
    ATTR_TOTAL_VOLUME,
    ATTR_WARNINGS,
    DOMAIN,
)
from .entity import PentairWaterEntity

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class PentairWaterSensorEntityDescription(SensorEntityDescription):
    """Describes Pentair Water Softener sensor entity."""

    value_fn: str  # Key in coordinator data


SENSOR_DESCRIPTIONS: tuple[PentairWaterSensorEntityDescription, ...] = (
    PentairWaterSensorEntityDescription(
        key="total_volume",
        translation_key="total_volume",
        native_unit_of_measurement=UnitOfVolume.LITERS,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=ATTR_TOTAL_VOLUME,
    ),
    PentairWaterSensorEntityDescription(
        key="last_regeneration",
        translation_key="last_regeneration",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=ATTR_LAST_REGENERATION,
    ),
    PentairWaterSensorEntityDescription(
        key="nr_regenerations",
        translation_key="nr_regenerations",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=ATTR_NR_REGENERATIONS,
    ),
    PentairWaterSensorEntityDescription(
        key="last_maintenance",
        translation_key="last_maintenance",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=ATTR_LAST_MAINTENANCE,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PentairWaterConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pentair Water Softener sensors."""
    coordinator = entry.runtime_data.coordinator

    entities: list[SensorEntity] = []

    # Add standard sensors
    for description in SENSOR_DESCRIPTIONS:
        entities.append(PentairWaterSensor(coordinator, entry, description))

    # Add warnings sensor
    entities.append(PentairWaterWarningsSensor(coordinator, entry))

    # Add flow sensor
    entities.append(PentairWaterFlowSensor(coordinator, entry))

    # Add status sensors
    entities.append(PentairWaterStatusSensor(coordinator, entry))
    entities.append(PentairWaterCapacityRemainingSensor(coordinator, entry))
    entities.append(PentairWaterDaysRemainingSensor(coordinator, entry))

    # Add water hardness sensor
    entities.append(PentairWaterHardnessSensor(coordinator, entry))

    # Add salt level sensor
    entities.append(PentairWaterSaltLevelSensor(coordinator, entry))

    # Add current flow rate sensor
    entities.append(PentairWaterCurrentFlowSensor(coordinator, entry))

    async_add_entities(entities)


class PentairWaterSensor(PentairWaterEntity, SensorEntity):
    """Representation of a Pentair Water Softener sensor."""

    entity_description: PentairWaterSensorEntityDescription

    def __init__(
        self,
        coordinator,
        entry: PentairWaterConfigEntry,
        description: PentairWaterSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self.entity_description = description
        self._attr_unique_id = f"{self._device_id}_{description.key}"

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None

        value = self.coordinator.data.get(self.entity_description.value_fn)

        # Handle timestamp conversion
        if self.entity_description.device_class == SensorDeviceClass.TIMESTAMP:
            if value:
                try:
                    return datetime.fromisoformat(value.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    return value

        # Handle numeric values
        if self.entity_description.state_class is not None:
            try:
                return int(value) if value is not None else None
            except (ValueError, TypeError):
                return value

        return value


class PentairWaterWarningsSensor(PentairWaterEntity, SensorEntity):
    """Sensor for displaying warnings."""

    _attr_translation_key = "warnings"

    def __init__(self, coordinator, entry: PentairWaterConfigEntry) -> None:
        """Initialize the warnings sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._device_id}_warnings"

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None

        warnings = self.coordinator.data.get(ATTR_WARNINGS, [])
        if not warnings:
            return None

        warning_text = ""
        for warning in warnings:
            description = warning.get("description", "")
            if description:
                warning_text += f"⚠️ {description}\n"

        return warning_text.strip() if warning_text else None


class PentairWaterFlowSensor(PentairWaterEntity, SensorEntity):
    """Sensor for water flow calculation."""

    _attr_translation_key = "flow"
    _attr_native_unit_of_measurement = UnitOfVolume.LITERS
    _attr_device_class = SensorDeviceClass.WATER
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, coordinator, entry: PentairWaterConfigEntry) -> None:
        """Initialize the flow sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._device_id}_flow"
        self._previous_value: int | None = None

    @property
    def native_value(self) -> int:
        """Return the flow since last update."""
        if self.coordinator.data is None:
            return 0

        current_value_str = self.coordinator.data.get(ATTR_TOTAL_VOLUME)
        if current_value_str is None:
            return 0

        try:
            current_value = int(str(current_value_str).split()[0])
        except (ValueError, TypeError):
            return 0

        if self._previous_value is None:
            self._previous_value = current_value
            return 0

        flow = current_value - self._previous_value
        self._previous_value = current_value

        return max(0, flow)  # Ensure non-negative


class PentairWaterStatusSensor(PentairWaterEntity, SensorEntity):
    """Sensor for device status."""

    _attr_translation_key = "status"

    def __init__(self, coordinator, entry: PentairWaterConfigEntry) -> None:
        """Initialize the status sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._device_id}_status"

    @property
    def native_value(self) -> str | None:
        """Return the status."""
        if self.coordinator.data is None:
            return None

        status = self.coordinator.data.get("status", {})
        return status.get("title")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional status attributes."""
        if self.coordinator.data is None:
            return {}

        status = self.coordinator.data.get("status", {})
        return {
            "status_code": status.get("code"),
            "percentage": status.get("percentage"),
        }


class PentairWaterCapacityRemainingSensor(PentairWaterEntity, SensorEntity):
    """Sensor for remaining capacity."""

    _attr_translation_key = "capacity_remaining"
    _attr_native_unit_of_measurement = UnitOfVolume.LITERS
    _attr_device_class = SensorDeviceClass.WATER
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry: PentairWaterConfigEntry) -> None:
        """Initialize the capacity remaining sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._device_id}_capacity_remaining"

    @property
    def native_value(self) -> int | None:
        """Return the remaining capacity."""
        if self.coordinator.data is None:
            return None

        status = self.coordinator.data.get("status", {})
        extra = status.get("extra", "")

        if extra:
            try:
                # Parse "1162 L" format
                return int(extra.split()[0])
            except (ValueError, IndexError):
                return None
        return None


class PentairWaterDaysRemainingSensor(PentairWaterEntity, SensorEntity):
    """Sensor for days until regeneration."""

    _attr_translation_key = "days_remaining"
    _attr_native_unit_of_measurement = "days"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry: PentairWaterConfigEntry) -> None:
        """Initialize the days remaining sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._device_id}_days_remaining"

    @property
    def native_value(self) -> int | None:
        """Return the days until regeneration."""
        if self.coordinator.data is None:
            return None

        status = self.coordinator.data.get("status", {})
        return status.get("days_remaining")


class PentairWaterHardnessSensor(PentairWaterEntity, SensorEntity):
    """Sensor for water hardness setting."""

    _attr_translation_key = "water_hardness"
    _attr_native_unit_of_measurement = "°dH"
    _attr_icon = "mdi:water-opacity"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry: PentairWaterConfigEntry) -> None:
        """Initialize the water hardness sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._device_id}_water_hardness"

    @property
    def native_value(self) -> float | None:
        """Return the water hardness."""
        if self.coordinator.data is None:
            return None

        hardness = self.coordinator.data.get("water_hardness")
        if hardness is not None:
            try:
                return float(hardness)
            except (ValueError, TypeError):
                return None
        return None


class PentairWaterSaltLevelSensor(PentairWaterEntity, SensorEntity):
    """Sensor for salt level."""

    _attr_translation_key = "salt_level"
    _attr_native_unit_of_measurement = "%"
    _attr_icon = "mdi:shaker"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry: PentairWaterConfigEntry) -> None:
        """Initialize the salt level sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._device_id}_salt_level"

    @property
    def native_value(self) -> int | None:
        """Return the salt level percentage."""
        if self.coordinator.data is None:
            return None

        salt_level = self.coordinator.data.get("salt_level")
        if salt_level is not None:
            try:
                return int(salt_level)
            except (ValueError, TypeError):
                return None
        return None


class PentairWaterCurrentFlowSensor(PentairWaterEntity, SensorEntity):
    """Sensor for current water flow rate."""

    _attr_translation_key = "current_flow"
    _attr_native_unit_of_measurement = "L/min"
    _attr_icon = "mdi:water-pump"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry: PentairWaterConfigEntry) -> None:
        """Initialize the current flow sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._device_id}_current_flow"

    @property
    def native_value(self) -> float | None:
        """Return the current flow rate."""
        if self.coordinator.data is None:
            return None

        flow_data = self.coordinator.data.get("flow", {})
        flow_rate = flow_data.get("flow_rate") or flow_data.get("current_flow") or flow_data.get("value")
        
        if flow_rate is not None:
            try:
                return float(flow_rate)
            except (ValueError, TypeError):
                return None
        return None


