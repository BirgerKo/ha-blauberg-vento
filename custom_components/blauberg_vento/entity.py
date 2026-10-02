"""Shared entity base for the Blauberg Vento integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from blauberg_vento import DeviceState

from .const import DOMAIN, MANUFACTURER
from .coordinator import VentoCoordinator


class VentoEntity(CoordinatorEntity[VentoCoordinator]):
    """Base entity for a Blauberg Vento device."""

    _attr_has_entity_name = True

    def __init__(self, entry: ConfigEntry, coordinator: VentoCoordinator) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.entry = entry
        state: DeviceState = coordinator.data
        self._device_id: str = entry.data["device_id"]
        self._attr_device_info = DeviceInfo(
            configuration_url=f"http://{entry.data['host']}",
            identifiers={(DOMAIN, self._device_id)},
            manufacturer=MANUFACTURER,
            model=state.unit_type_name if state.unit_type else None,
            name=self._device_id,
            sw_version=str(state.firmware) if state.firmware else None,
        )

    @property
    def available(self) -> bool:
        """Return True if the coordinator has data."""
        return self.coordinator.last_update_success and self.coordinator.data is not None

    @property
    def vento_state(self) -> DeviceState:
        """Return the current device state."""
        return self.coordinator.data

    @property
    def client(self):
        """Return the async client shared by the coordinator."""
        return self.coordinator.client
