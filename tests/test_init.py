"""Tests for setting up and unloading the integration."""

from __future__ import annotations

from unittest.mock import AsyncMock

import homeassistant.util.dt as dt_util
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from blauberg_vento import VentoError

from .conftest import DEVICE_ID, setup_integration


async def test_setup_and_unload(
    hass: HomeAssistant, config_entry, mock_client
) -> None:
    """The integration sets up and unloads cleanly."""
    await setup_integration(hass, config_entry, mock_client)
    assert config_entry.state is ConfigEntryState.LOADED

    fan = hass.states.get(f"fan.{DEVICE_ID.lower()}")
    assert fan is not None
    assert fan.state == "on"

    humidity = hass.states.get(f"sensor.{DEVICE_ID.lower()}_humidity")
    assert humidity is not None
    assert humidity.state == "55"

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.NOT_LOADED


async def test_entities_unavailable_on_error(
    hass: HomeAssistant, config_entry, mock_client
) -> None:
    """Entities become unavailable when the device stops responding."""
    from custom_components.blauberg_vento.coordinator import SCAN_INTERVAL

    await setup_integration(hass, config_entry, mock_client)
    mock_client.get_state = AsyncMock(side_effect=VentoError("timeout"))

    async_fire_time_changed(hass, dt_util.utcnow() + SCAN_INTERVAL)
    await hass.async_block_till_done()

    fan = hass.states.get(f"fan.{DEVICE_ID.lower()}")
    assert fan is not None
    assert fan.state == "unavailable"
