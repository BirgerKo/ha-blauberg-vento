"""The Blauberg Vento integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from blauberg_vento import AsyncVentoClient

from .const import CONF_DEVICE_ID, CONF_HOST, CONF_PASSWORD
from .coordinator import VentoCoordinator

PLATFORMS = ("binary_sensor", "button", "fan", "number", "select", "sensor", "switch")


@dataclass
class BlaubergVentoData:
    """Runtime data stored on a config entry."""

    client: AsyncVentoClient
    coordinator: VentoCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a Blauberg Vento device from a config entry."""
    client = AsyncVentoClient(
        host=entry.data[CONF_HOST],
        device_id=entry.data[CONF_DEVICE_ID],
        password=entry.data[CONF_PASSWORD],
    )
    coordinator = VentoCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = BlaubergVentoData(client=client, coordinator=coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Blauberg Vento config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return unload_ok
