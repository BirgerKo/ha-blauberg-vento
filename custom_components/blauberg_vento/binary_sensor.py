"""Binary sensor platform for the Blauberg Vento integration."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
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
    """Set up the binary sensor platform."""
    coordinator: VentoCoordinator = entry.runtime_data.coordinator
    async_add_entities(
        [
            VentoFilterBinarySensor(entry, coordinator),
            VentoRelayBinarySensor(entry, coordinator),
            VentoBoostBinarySensor(entry, coordinator),
        ]
    )


class VentoFilterBinarySensor(VentoEntity, BinarySensorEntity):
    """Filter replacement indicator."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "filter_needs_replacement"

    def __init__(self, entry: ConfigEntry, coordinator: VentoCoordinator) -> None:
        """Initialize the binary sensor."""
        super().__init__(entry, coordinator)
        self._attr_unique_id = f"{self._device_id}_filter_needs_replacement"
        self._attr_name = "Filter needs replacement"

    @property
    def is_on(self) -> bool | None:
        """Return True if the filter needs replacement."""
        return self.vento_state.filter_needs_replacement


class VentoRelayBinarySensor(VentoEntity, BinarySensorEntity):
    """External relay input state."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = BinarySensorDeviceClass.PLUG
    _attr_translation_key = "relay_state"

    def __init__(self, entry: ConfigEntry, coordinator: VentoCoordinator) -> None:
        """Initialize the binary sensor."""
        super().__init__(entry, coordinator)
        self._attr_unique_id = f"{self._device_id}_relay_state"
        self._attr_name = "Relay"

    @property
    def is_on(self) -> bool | None:
        """Return True if the relay input is active."""
        return self.vento_state.relay_state


class VentoBoostBinarySensor(VentoEntity, BinarySensorEntity):
    """Boost mode indicator."""

    _attr_translation_key = "boost_active"

    def __init__(self, entry: ConfigEntry, coordinator: VentoCoordinator) -> None:
        """Initialize the binary sensor."""
        super().__init__(entry, coordinator)
        self._attr_unique_id = f"{self._device_id}_boost_active"
        self._attr_name = "Boost"

    @property
    def is_on(self) -> bool | None:
        """Return True if boost mode is active."""
        return self.vento_state.boost_active
