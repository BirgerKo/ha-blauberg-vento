"""Tests for the sensor and binary sensor platforms."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from .conftest import DEVICE_ID, create_device_state, create_mock_client, setup_integration

ENTITY_BASE = DEVICE_ID.lower()


async def test_sensors(hass: HomeAssistant, config_entry, mock_client) -> None:
    """Sensor entities report the device state."""
    await setup_integration(hass, config_entry, mock_client)

    expected = {
        f"sensor.{ENTITY_BASE}_humidity": "55",
        f"sensor.{ENTITY_BASE}_fan_1_rpm": "1230",
        f"sensor.{ENTITY_BASE}_fan_2_rpm": "1210",
        f"sensor.{ENTITY_BASE}_machine_hours": "291.5",
        f"sensor.{ENTITY_BASE}_alarm_status": "ok",
        f"sensor.{ENTITY_BASE}_firmware": "3.2 (24-06-15)",
    }
    for entity_id, value in expected.items():
        state = hass.states.get(entity_id)
        assert state is not None, entity_id
        assert state.state == value, entity_id

    filter_countdown = hass.states.get(f"sensor.{ENTITY_BASE}_filter_countdown")
    assert filter_countdown is not None
    assert abs(float(filter_countdown.state) - 90.2083) < 0.01


async def test_binary_sensors(hass: HomeAssistant, config_entry, mock_client) -> None:
    """Binary sensor entities report the device state."""
    await setup_integration(hass, config_entry, mock_client)

    expected = {
        f"binary_sensor.{ENTITY_BASE}_filter_needs_replacement": "off",
        f"binary_sensor.{ENTITY_BASE}_relay": "off",
        f"binary_sensor.{ENTITY_BASE}_boost": "off",
    }
    for entity_id, value in expected.items():
        state = hass.states.get(entity_id)
        assert state is not None, entity_id
        assert state.state == value, entity_id


async def test_missing_attributes_report_unknown(
    hass: HomeAssistant, config_entry
) -> None:
    """Sensors report unknown when the device does not provide a value."""
    state = create_device_state(
        fan2_rpm=None, filter_countdown=None, machine_hours=None, firmware=None
    )
    client = create_mock_client(state)
    await setup_integration(hass, config_entry, client)

    assert hass.states.get(f"sensor.{ENTITY_BASE}_fan_2_rpm").state == "unknown"
    assert hass.states.get(f"sensor.{ENTITY_BASE}_filter_countdown").state == "unknown"
    assert hass.states.get(f"sensor.{ENTITY_BASE}_machine_hours").state == "unknown"
    assert hass.states.get(f"sensor.{ENTITY_BASE}_firmware").state == "unknown"
