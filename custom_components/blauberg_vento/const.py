"""Constants for the Blauberg Vento integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "blauberg_vento"
MANUFACTURER = "Blauberg"

CONF_DEVICE_ID = "device_id"
CONF_HOST = "host"
CONF_PASSWORD = "password"

DEFAULT_PASSWORD = "1111"

# The protocol accepts reads addressed to this ID before the real device
# ID is known; it is used for validation during the config flow.
DEFAULT_DEVICE_ID = "DEFAULT_DEVICEID"

SCAN_INTERVAL = timedelta(seconds=30)
DISCOVERY_TIMEOUT = 3.0

OPERATION_MODE_VENTILATION = "ventilation"
OPERATION_MODE_HEAT_RECOVERY = "heat_recovery"
OPERATION_MODE_SUPPLY = "supply"
