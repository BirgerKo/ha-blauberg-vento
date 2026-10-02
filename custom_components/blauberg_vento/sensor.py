"""Sensor platform for the Blauberg Vento integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import VentoCoordinator
from .entity import VentoEntity

ALARM_OPTIONS = ["ok", "warning", "alarm"]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: VentoCoordinator = entry.runtime_data.coordinator
    entities: list[SensorEntity] = [
        VentoHumiditySensor(entry, coordinator),
        VentoRpmSensor(entry, coordinator, fan=1),
        VentoRpmSensor(entry, coordinator, fan=2),
        VentoFilterCountdownSensor(entry, coordinator),
        VentoMachineHoursSensor(entry, coordinator),
        VentoAlarmSensor(entry, coordinator),
        VentoFirmwareSensor(entry, coordinator),
    ]
    async_add_entities(entities)


class VentoHumiditySensor(VentoEntity, SensorEntity):
    """Current humidity measured by the device."""

    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:water-percent"

    def __init__(self, entry: ConfigEntry, coordinator: VentoCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(entry, coordinator)
        self._attr_unique_id = f"{self._device_id}_humidity"
        self._attr_name = "Humidity"

    @property
    def native_value(self) -> int | None:
        """Return the current humidity."""
        return self.vento_state.current_humidity


class VentoRpmSensor(VentoEntity, SensorEntity):
    """Fan speed in RPM."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:fan"

    def __init__(self, entry: ConfigEntry, coordinator: VentoCoordinator, fan: int) -> None:
        """Initialize the sensor."""
        super().__init__(entry, coordinator)
        self._fan = fan
        self._attr_unique_id = f"{self._device_id}_fan{fan}_rpm"
        self._attr_name = f"Fan {fan} RPM"

    @property
    def native_value(self) -> int | None:
        """Return the fan RPM."""
        if self._fan == 1:
            return self.vento_state.fan1_rpm
        return self.vento_state.fan2_rpm


class VentoFilterCountdownSensor(VentoEntity, SensorEntity):
    """Time remaining until the filter needs replacement."""

    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTime.DAYS
    _attr_icon = "mdi:air-filter"

    def __init__(self, entry: ConfigEntry, coordinator: VentoCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(entry, coordinator)
        self._attr_unique_id = f"{self._device_id}_filter_countdown"
        self._attr_name = "Filter countdown"

    @property
    def native_value(self) -> float | None:
        """Return the remaining filter time in days."""
        countdown = self.vento_state.filter_countdown
        if countdown is None:
            return None
        return countdown.days + countdown.hours / 24 + countdown.minutes / 1440


class VentoMachineHoursSensor(VentoEntity, SensorEntity):
    """Total runtime of the device."""

    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_icon = "mdi:clock-outline"

    def __init__(self, entry: ConfigEntry, coordinator: VentoCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(entry, coordinator)
        self._attr_unique_id = f"{self._device_id}_machine_hours"
        self._attr_name = "Machine hours"

    @property
    def native_value(self) -> float | None:
        """Return total machine hours."""
        machine_hours = self.vento_state.machine_hours
        if machine_hours is None:
            return None
        return round(machine_hours.total_hours(), 2)


class VentoAlarmSensor(VentoEntity, SensorEntity):
    """Device alarm status."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ALARM_OPTIONS
    _attr_translation_key = "alarm_status"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:alert-circle-outline"

    def __init__(self, entry: ConfigEntry, coordinator: VentoCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(entry, coordinator)
        self._attr_unique_id = f"{self._device_id}_alarm_status"
        self._attr_name = "Alarm status"

    @property
    def native_value(self) -> str | None:
        """Return the alarm status."""
        status = self.vento_state.alarm_status
        if status == 0:
            return "ok"
        if status == 2:
            return "warning"
        if status == 1:
            return "alarm"
        return None


class VentoFirmwareSensor(VentoEntity, SensorEntity):
    """Device firmware version."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:chip"

    def __init__(self, entry: ConfigEntry, coordinator: VentoCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(entry, coordinator)
        self._attr_unique_id = f"{self._device_id}_firmware"
        self._attr_name = "Firmware"

    @property
    def native_value(self) -> str | None:
        """Return the firmware version."""
        firmware = self.vento_state.firmware
        return str(firmware) if firmware else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return firmware metadata."""
        firmware = self.vento_state.firmware
        if firmware is None:
            return {}
        return {"raw": f"{firmware.major}.{firmware.minor}"}
