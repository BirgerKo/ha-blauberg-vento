"""Switch platform for the Blauberg Vento integration."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import VentoCoordinator
from .entity import VentoEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch platform."""
    coordinator: VentoCoordinator = entry.runtime_data.coordinator
    async_add_entities([VentoScheduleSwitch(entry, coordinator)])


class VentoScheduleSwitch(VentoEntity, SwitchEntity):
    """Toggle the device weekly schedule."""

    _attr_icon = "mdi:calendar-clock"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "weekly_schedule"

    def __init__(self, entry: ConfigEntry, coordinator: VentoCoordinator) -> None:
        """Initialize the switch."""
        super().__init__(entry, coordinator)
        self._attr_unique_id = f"{self._device_id}_weekly_schedule"
        self._attr_name = "Weekly schedule"

    @property
    def is_on(self) -> bool | None:
        """Return True if the weekly schedule is enabled."""
        return self.vento_state.weekly_schedule_enabled

    async def async_turn_on(self, **kwargs) -> None:
        """Enable the weekly schedule."""
        await self.client.enable_weekly_schedule(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Disable the weekly schedule."""
        await self.client.enable_weekly_schedule(False)
        await self.coordinator.async_request_refresh()
