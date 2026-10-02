"""Tests for the fan platform."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from .conftest import DEVICE_ID, setup_integration


async def test_fan_state(
    hass: HomeAssistant, config_entry, mock_client
) -> None:
    """The fan reflects the device state."""
    await setup_integration(hass, config_entry, mock_client)

    state = hass.states.get(f"fan.{DEVICE_ID.lower()}")
    assert state is not None
    assert state.state == "on"
    assert state.attributes["percentage"] == 67


async def test_fan_set_percentage(
    hass: HomeAssistant, config_entry, mock_client
) -> None:
    """Setting a percentage maps to a device speed."""
    await setup_integration(hass, config_entry, mock_client)

    await hass.services.async_call(
        "fan",
        "set_percentage",
        {"entity_id": f"fan.{DEVICE_ID.lower()}", "percentage": 100},
        blocking=True,
    )
    assert mock_client.set_speed.call_args.args == (3,)


async def test_fan_turn_off_and_on(
    hass: HomeAssistant, config_entry, mock_client
) -> None:
    """Turn off and turn on are forwarded to the device."""
    await setup_integration(hass, config_entry, mock_client)

    await hass.services.async_call(
        "fan",
        "turn_off",
        {"entity_id": f"fan.{DEVICE_ID.lower()}"},
        blocking=True,
    )
    mock_client.turn_off.assert_awaited_once()

    await hass.services.async_call(
        "fan",
        "turn_on",
        {"entity_id": f"fan.{DEVICE_ID.lower()}"},
        blocking=True,
    )
    mock_client.turn_on.assert_awaited_once()
