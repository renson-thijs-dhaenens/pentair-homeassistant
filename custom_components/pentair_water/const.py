"""Constants for Pentair Water Softener integration."""
from datetime import timedelta
from typing import Final

DOMAIN: Final = "pentair_water"
MANUFACTURER: Final = "Pentair"
DEFAULT_NAME: Final = "Pentair Water Softener"

# Scan interval for polling
DEFAULT_SCAN_INTERVAL: Final = 120  # seconds
SCAN_INTERVAL: Final = timedelta(seconds=DEFAULT_SCAN_INTERVAL)

# Config entry keys
CONF_EMAIL: Final = "email"
CONF_PASSWORD: Final = "password"
CONF_ACCESS_TOKEN: Final = "access_token"
CONF_CLIENT_ID: Final = "client_id"
CONF_UID: Final = "uid"
CONF_EXPIRY: Final = "expiry"
CONF_DEVICE_ID: Final = "device_id"
CONF_DEVICE_NAME: Final = "device_name"
CONF_SCAN_INTERVAL: Final = "scan_interval"

# Data keys
DATA_COORDINATOR: Final = "coordinator"
DATA_API: Final = "api"

# Sensor types
ATTR_LAST_REGENERATION: Final = "last_regeneration"
ATTR_NR_REGENERATIONS: Final = "nr_regenerations"
ATTR_LAST_MAINTENANCE: Final = "last_maintenance"
ATTR_TOTAL_VOLUME: Final = "total_volume"
ATTR_WARNINGS: Final = "warnings"
ATTR_LOW_SALT: Final = "low_salt"
ATTR_SETTINGS: Final = "settings"
ATTR_HOLIDAY_MODE: Final = "holiday_mode"
ATTR_WATER_HARDNESS: Final = "water_hardness"
ATTR_FLOW: Final = "flow"
