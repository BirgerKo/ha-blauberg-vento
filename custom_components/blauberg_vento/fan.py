"""Fan platform for the Blauberg Vento integration."""

from __future__ import annotations

import math

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import VentoCoordinator
from .entity import VentoEntity

SPEED_STEP = 100 / 3


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the fan platform."""
    coordinator: VentoCoordinator = entry.runtime_data.coordinator
    async_add_entities([VentoFan(entry, coordinator)])


class VentoFan(VentoEntity, FanEntity):
    """Representation of a Blauberg Vento fan."""

    _attr_supported_features = (
        FanEntityFeature.SET_SPEED | FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF
    )
    _attr_speed_count = 3

    def __init__(self, entry: ConfigEntry, coordinator: VentoCoordinator) -> None:
        """Initialize the fan."""
        super().__init__(entry, coordinator)
        self._attr_unique_id = f"{self._device_id}_fan"
        self._attr_name = None

    @property
    def is_on(self) -> bool | None:
        """Return True if the fan is on."""
        return self.vento_state.power

    @property
    def percentage(self) -> int | None:
        """Return the current speed as a percentage."""
        state = self.vento_state
        if state.power is not True:
            return None
        if state.speed == 255:
            manual = state.manual_speed or 0
            return round(manual / 255 * 100)
        if state.speed in (1, 2, 3):
            return round(SPEED_STEP * state.speed)
        return None

    async def async_turn_on(
        self, percentage: int | None = None, preset_mode: str | None = None, **kwargs
    ) -> None:
        """Turn the fan on."""
        if percentage is not None:
            await self.async_set_percentage(percentage)
            return
        await self.client.turn_on()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the fan off."""
        await self.client.turn_off()
        await self.coordinator.async_request_refresh()

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed of the fan."""
        if percentage == 0:
            await self.async_turn_off()
            return
        if self.vento_state.power is not True:
            await self.client.turn_on()
        speed = min(3, max(1, math.ceil(percentage / SPEED_STEP)))
        await self.client.set_speed(speed)
        await self.coordinator.async_request_refresh()
