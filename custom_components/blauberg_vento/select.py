"""Select platform for the Blauberg Vento integration."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    OPERATION_MODE_HEAT_RECOVERY,
    OPERATION_MODE_SUPPLY,
    OPERATION_MODE_VENTILATION,
)
from .coordinator import VentoCoordinator
from .entity import VentoEntity

OPERATION_MODES: dict[int, str] = {
    0: OPERATION_MODE_VENTILATION,
    1: OPERATION_MODE_HEAT_RECOVERY,
    2: OPERATION_MODE_SUPPLY,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the select platform."""
    coordinator: VentoCoordinator = entry.runtime_data.coordinator
    async_add_entities([VentoOperationModeSelect(entry, coordinator)])


class VentoOperationModeSelect(VentoEntity, SelectEntity):
    """Select for the device operation mode."""

    _attr_icon = "mdi:hvac"
    _attr_options = list(OPERATION_MODES.values())
    _attr_translation_key = "operation_mode"

    def __init__(self, entry: ConfigEntry, coordinator: VentoCoordinator) -> None:
        """Initialize the select."""
        super().__init__(entry, coordinator)
        self._attr_unique_id = f"{self._device_id}_operation_mode"
        self._attr_name = "Operation mode"

    @property
    def current_option(self) -> str | None:
        """Return the current operation mode."""
        return OPERATION_MODES.get(self.vento_state.operation_mode or 0)

    async def async_select_option(self, option: str) -> None:
        """Set the operation mode."""
        mode = next((m for m, name in OPERATION_MODES.items() if name == option), None)
        if mode is not None:
            await self.client.set_mode(mode)
            await self.coordinator.async_request_refresh()
