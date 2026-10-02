"""Shared fixtures for Blauberg Vento tests."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from custom_components.blauberg_vento.const import (
    CONF_DEVICE_ID,
    CONF_HOST,
    CONF_PASSWORD,
    DOMAIN,
)
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from blauberg_vento import DeviceState, FilterCountdown, FirmwareVersion, MachineHours

pytest_plugins = ("pytest_homeassistant_custom_component",)

DEVICE_ID = "BVZ01A5010123456"
HOST = "192.168.1.42"
PASSWORD = "1111"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading custom integrations in all tests."""
    yield


def create_device_state(**overrides: Any) -> DeviceState:
    """Create a fully populated DeviceState for testing."""
    state = DeviceState(
        ip=HOST,
        device_id=DEVICE_ID,
        unit_type=3,
        power=True,
        speed=2,
        manual_speed=120,
        operation_mode=0,
        boost_active=False,
        boost_delay_minutes=30,
        current_humidity=55,
        humidity_threshold=60,
        fan1_rpm=1230,
        fan2_rpm=1210,
        filter_countdown=FilterCountdown(days=90, hours=5, minutes=0),
        filter_needs_replacement=False,
        alarm_status=0,
        machine_hours=MachineHours(days=12, hours=3, minutes=30),
        relay_state=False,
        weekly_schedule_enabled=True,
        firmware=FirmwareVersion(major=3, minor=2, day=15, month=6, year=24),
    )
    for key, value in overrides.items():
        setattr(state, key, value)
    return state


def create_mock_client(state: DeviceState | None = None) -> MagicMock:
    """Create a mock AsyncVentoClient."""
    client = MagicMock()
    if state is None:
        state = create_device_state()
    client.get_state = AsyncMock(return_value=state)
    client.turn_on = AsyncMock()
    client.turn_off = AsyncMock()
    client.set_speed = AsyncMock()
    client.set_manual_speed = AsyncMock()
    client.set_mode = AsyncMock()
    client.set_humidity_threshold = AsyncMock()
    client.set_boost_delay = AsyncMock()
    client.enable_weekly_schedule = AsyncMock()
    client.reset_filter_timer = AsyncMock()
    client.reset_alarms = AsyncMock()
    client.read_params = AsyncMock()
    return client


@pytest.fixture
def mock_client() -> MagicMock:
    """Return a default mock client."""
    return create_mock_client()


@pytest.fixture
def config_entry() -> MockConfigEntry:
    """Return a configured mock entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=DEVICE_ID,
        data={
            CONF_HOST: HOST,
            CONF_PASSWORD: PASSWORD,
            CONF_DEVICE_ID: DEVICE_ID,
        },
        unique_id=DEVICE_ID,
    )


async def setup_integration(
    hass: HomeAssistant, entry: MockConfigEntry, client: MagicMock
) -> MockConfigEntry:
    """Set up the integration with a mocked client."""
    entry.add_to_hass(hass)
    with patch(
        "custom_components.blauberg_vento.AsyncVentoClient",
        return_value=client,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry
