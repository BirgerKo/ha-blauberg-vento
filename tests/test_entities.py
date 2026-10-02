"""Tests for the select, number, switch and button platforms."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from .conftest import DEVICE_ID, setup_integration

ENTITY_BASE = DEVICE_ID.lower()


async def _call(hass: HomeAssistant, domain: str, service: str, data: dict) -> None:
    await hass.services.async_call(domain, service, data, blocking=True)


async def test_select_operation_mode(
    hass: HomeAssistant, config_entry, mock_client
) -> None:
    """The operation mode select maps to device modes."""
    await setup_integration(hass, config_entry, mock_client)

    state = hass.states.get(f"select.{ENTITY_BASE}_operation_mode")
    assert state is not None
    assert state.state == "ventilation"
    assert set(state.attributes["options"]) == {"ventilation", "heat_recovery", "supply"}

    await _call(
        hass,
        "select",
        "select_option",
        {
            "entity_id": f"select.{ENTITY_BASE}_operation_mode",
            "option": "heat_recovery",
        },
    )
    mock_client.set_mode.assert_awaited_once_with(1)


async def test_numbers(
    hass: HomeAssistant, config_entry, mock_client
) -> None:
    """Number entities expose and set device parameters."""
    await setup_integration(hass, config_entry, mock_client)

    humidity = hass.states.get(f"number.{ENTITY_BASE}_humidity_threshold")
    assert humidity is not None
    assert humidity.state == "60"
    await _call(
        hass,
        "number",
        "set_value",
        {"entity_id": f"number.{ENTITY_BASE}_humidity_threshold", "value": 65},
    )
    mock_client.set_humidity_threshold.assert_awaited_once_with(65)

    boost_delay = hass.states.get(f"number.{ENTITY_BASE}_boost_delay")
    assert boost_delay is not None
    assert boost_delay.state == "30"
    await _call(
        hass,
        "number",
        "set_value",
        {"entity_id": f"number.{ENTITY_BASE}_boost_delay", "value": 15},
    )
    mock_client.set_boost_delay.assert_awaited_once_with(15)

    manual_speed = hass.states.get(f"number.{ENTITY_BASE}_manual_speed")
    assert manual_speed is not None
    assert manual_speed.state == "120"
    await _call(
        hass,
        "number",
        "set_value",
        {"entity_id": f"number.{ENTITY_BASE}_manual_speed", "value": 200},
    )
    mock_client.set_manual_speed.assert_awaited_once_with(200)


async def test_switch_weekly_schedule(
    hass: HomeAssistant, config_entry, mock_client
) -> None:
    """The weekly schedule switch toggles the device schedule."""
    await setup_integration(hass, config_entry, mock_client)

    state = hass.states.get(f"switch.{ENTITY_BASE}_weekly_schedule")
    assert state is not None
    assert state.state == "on"

    await _call(
        hass,
        "switch",
        "turn_off",
        {"entity_id": f"switch.{ENTITY_BASE}_weekly_schedule"},
    )
    mock_client.enable_weekly_schedule.assert_awaited_once_with(False)


async def test_buttons(
    hass: HomeAssistant, config_entry, mock_client
) -> None:
    """Buttons trigger device actions."""
    await setup_integration(hass, config_entry, mock_client)

    await _call(
        hass,
        "button",
        "press",
        {"entity_id": f"button.{ENTITY_BASE}_reset_filter_timer"},
    )
    mock_client.reset_filter_timer.assert_awaited_once()

    await _call(
        hass,
        "button",
        "press",
        {"entity_id": f"button.{ENTITY_BASE}_reset_alarms"},
    )
    mock_client.reset_alarms.assert_awaited_once()
