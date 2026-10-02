"""Number platform for the Blauberg Vento integration."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import VentoCoordinator
from .entity import VentoEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the number platform."""
    coordinator: VentoCoordinator = entry.runtime_data.coordinator
    async_add_entities(
        [
            VentoHumidityThresholdNumber(entry, coordinator),
            VentoBoostDelayNumber(entry, coordinator),
            VentoManualSpeedNumber(entry, coordinator),
        ]
    )


class VentoHumidityThresholdNumber(VentoEntity, NumberEntity):
    """Humidity threshold for automatic speed control."""

    _attr_icon = "mdi:water-percent"
    _attr_native_min_value = 40
    _attr_native_max_value = 80
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "%"
    _attr_mode = NumberMode.SLIDER
    _attr_translation_key = "humidity_threshold"

    def __init__(self, entry: ConfigEntry, coordinator: VentoCoordinator) -> None:
        """Initialize the number entity."""
        super().__init__(entry, coordinator)
        self._attr_unique_id = f"{self._device_id}_humidity_threshold"
        self._attr_name = "Humidity threshold"

    @property
    def native_value(self) -> float | None:
        """Return the current threshold."""
        return self.vento_state.humidity_threshold

    async def async_set_native_value(self, value: float) -> None:
        """Set the humidity threshold."""
        await self.client.set_humidity_threshold(round(value))
        await self.coordinator.async_request_refresh()


class VentoBoostDelayNumber(VentoEntity, NumberEntity):
    """Boost duration in minutes."""

    _attr_icon = "mdi:fast-forward-60"
    _attr_native_min_value = 0
    _attr_native_max_value = 60
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "min"
    _attr_mode = NumberMode.SLIDER
    _attr_translation_key = "boost_delay"

    def __init__(self, entry: ConfigEntry, coordinator: VentoCoordinator) -> None:
        """Initialize the number entity."""
        super().__init__(entry, coordinator)
        self._attr_unique_id = f"{self._device_id}_boost_delay"
        self._attr_name = "Boost delay"

    @property
    def native_value(self) -> float | None:
        """Return the boost delay."""
        return self.vento_state.boost_delay_minutes

    async def async_set_native_value(self, value: float) -> None:
        """Set the boost delay."""
        await self.client.set_boost_delay(round(value))
        await self.coordinator.async_request_refresh()


class VentoManualSpeedNumber(VentoEntity, NumberEntity):
    """Manual fan speed (0-255) used in manual speed mode."""

    _attr_icon = "mdi:tune"
    _attr_native_min_value = 0
    _attr_native_max_value = 255
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX
    _attr_translation_key = "manual_speed"

    def __init__(self, entry: ConfigEntry, coordinator: VentoCoordinator) -> None:
        """Initialize the number entity."""
        super().__init__(entry, coordinator)
        self._attr_unique_id = f"{self._device_id}_manual_speed"
        self._attr_name = "Manual speed"

    @property
    def native_value(self) -> float | None:
        """Return the manual speed."""
        return self.vento_state.manual_speed

    async def async_set_native_value(self, value: float) -> None:
        """Set the manual speed and switch to manual mode."""
        await self.client.set_manual_speed(round(value))
        await self.coordinator.async_request_refresh()
