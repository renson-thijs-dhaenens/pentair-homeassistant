"""DataUpdateCoordinator for Pentair Water Softener."""
from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

if TYPE_CHECKING:
    from . import PentairWaterConfigEntry


def get_coordinator(entry: PentairWaterConfigEntry) -> DataUpdateCoordinator:
    """Get the data update coordinator."""
    return entry.runtime_data.coordinator
