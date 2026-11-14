"""Tests for the coordinator's failure classification."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from custom_components.blauberg_vento.auth import ProbeAuthError, ProbeConnectionError
from custom_components.blauberg_vento.coordinator import VentoCoordinator
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed

from blauberg_vento import VentoError

from .conftest import DEVICE_ID, HOST, PASSWORD, create_mock_client


def _failing_client() -> MagicMock:
    client = create_mock_client()
    client.host = HOST
    client.device_id = DEVICE_ID
    client.password = PASSWORD
    client.get_state = AsyncMock(side_effect=VentoError("protocol error"))
    return client


async def test_poll_auth_rejection_raises_config_entry_auth_failed(
    hass: HomeAssistant, mock_credential_probe
) -> None:
    """A FUNC 0x07 rejection during a poll starts the reauth flow."""
    mock_credential_probe.coordinator.side_effect = ProbeAuthError("rejected")
    coordinator = VentoCoordinator(hass, _failing_client())

    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()


async def test_poll_silent_device_stays_update_failed(
    hass: HomeAssistant, mock_credential_probe
) -> None:
    """A device that does not answer is a network fault, not an auth fault."""
    mock_credential_probe.coordinator.side_effect = ProbeConnectionError("no reply")
    coordinator = VentoCoordinator(hass, _failing_client())

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


async def test_poll_failure_with_working_credentials_stays_update_failed(
    hass: HomeAssistant, mock_credential_probe
) -> None:
    """A failed poll whose probe succeeds stays a plain update failure."""
    coordinator = VentoCoordinator(hass, _failing_client())

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()
