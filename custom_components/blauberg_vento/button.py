"""Button platform for the Blauberg Vento integration."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
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
    """Set up the button platform."""
    coordinator: VentoCoordinator = entry.runtime_data.coordinator
    async_add_entities(
        [
            VentoFilterResetButton(entry, coordinator),
            VentoResetAlarmsButton(entry, coordinator),
        ]
    )


class VentoFilterResetButton(VentoEntity, ButtonEntity):
    """Reset the filter replacement countdown."""

    _attr_icon = "mdi:air-filter"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "filter_reset"

    def __init__(self, entry: ConfigEntry, coordinator: VentoCoordinator) -> None:
        """Initialize the button."""
        super().__init__(entry, coordinator)
        self._attr_unique_id = f"{self._device_id}_filter_reset"
        self._attr_name = "Reset filter timer"

    async def async_press(self) -> None:
        """Reset the filter timer."""
        await self.client.reset_filter_timer()
        await self.coordinator.async_request_refresh()


class VentoResetAlarmsButton(VentoEntity, ButtonEntity):
    """Clear device alarms."""

    _attr_icon = "mdi:bell-off"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "reset_alarms"

    def __init__(self, entry: ConfigEntry, coordinator: VentoCoordinator) -> None:
        """Initialize the button."""
        super().__init__(entry, coordinator)
        self._attr_unique_id = f"{self._device_id}_reset_alarms"
        self._attr_name = "Reset alarms"

    async def async_press(self) -> None:
        """Reset the alarms."""
        await self.client.reset_alarms()
        await self.coordinator.async_request_refresh()
