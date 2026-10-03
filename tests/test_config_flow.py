"""Tests for the Blauberg Vento config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from custom_components.blauberg_vento.const import DOMAIN
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from blauberg_vento import DiscoveredDevice, Param, VentoError

from .conftest import DEVICE_ID, HOST

READ_PARAMS_OK = {Param.DEVICE_SEARCH: DEVICE_ID.encode()}


def patched_discovery(devices: list[DiscoveredDevice]):
    """Patch discovery to return the given devices."""
    return patch(
        "custom_components.blauberg_vento.config_flow.AsyncVentoClient.discover",
        return_value=devices,
    )


def patched_read_params(side_effect=None, return_value=None):
    """Patch the client read used for credential validation."""
    target = "custom_components.blauberg_vento.config_flow.AsyncVentoClient.read_params"
    if side_effect is not None:
        return patch(target, new=AsyncMock(side_effect=side_effect))
    return patch(target, new=AsyncMock(return_value=return_value))


async def test_flow_discovery_finds_device(hass: HomeAssistant) -> None:
    """Discovery shows the device picker when devices are found."""
    with patched_discovery([DiscoveredDevice(ip=HOST, device_id=DEVICE_ID, unit_type=3)]):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "discovery"


async def test_flow_no_devices_shows_manual_form(hass: HomeAssistant) -> None:
    """The manual form is shown when discovery finds nothing."""
    with patched_discovery([]):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "no_devices_found"}


async def test_flow_discovered_device_requires_password(hass: HomeAssistant) -> None:
    """Picking a discovered device asks for the password."""
    with patched_discovery([DiscoveredDevice(ip=HOST, device_id=DEVICE_ID, unit_type=3)]):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": HOST}
        )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "credentials"


async def test_flow_discovered_device_validates_credentials(hass: HomeAssistant) -> None:
    """A wrong password does not create an entry for a discovered device."""
    with patched_discovery(
        [DiscoveredDevice(ip=HOST, device_id=DEVICE_ID, unit_type=3)]
    ), patched_read_params(side_effect=VentoError("timeout")):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": HOST}
        )
        assert result["step_id"] == "credentials"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"password": "9999"}
        )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "credentials"
    assert result["errors"] == {"base": "cannot_connect"}
    assert len(hass.config_entries.async_entries(DOMAIN)) == 0


async def test_flow_discovered_device_creates_entry(hass: HomeAssistant) -> None:
    """A discovered device with valid credentials creates an entry."""
    with patched_discovery(
        [DiscoveredDevice(ip=HOST, device_id=DEVICE_ID, unit_type=3)]
    ), patched_read_params(return_value=READ_PARAMS_OK):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": HOST}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"password": "1234"}
        )
        await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == DEVICE_ID
    assert result["data"] == {
        "host": HOST,
        "password": "1234",
        "device_id": DEVICE_ID,
    }


async def test_flow_manual_entry_creates_entry(hass: HomeAssistant) -> None:
    """A manually entered host is validated and creates an entry."""
    with patched_discovery([]), patched_read_params(return_value=READ_PARAMS_OK):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": HOST, "password": "1111"}
        )
        await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == DEVICE_ID
    assert result["data"] == {
        "host": HOST,
        "password": "1111",
        "device_id": DEVICE_ID,
    }


async def test_flow_manual_entry_cannot_connect(hass: HomeAssistant) -> None:
    """A connection failure shows the manual form with an error."""
    with patched_discovery([]), patched_read_params(side_effect=VentoError("timeout")):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": HOST, "password": "1111"}
        )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_flow_already_configured_aborts(hass: HomeAssistant) -> None:
    """A duplicate device aborts the flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"host": HOST, "password": "1111", "device_id": DEVICE_ID},
        unique_id=DEVICE_ID,
    )
    entry.add_to_hass(hass)

    with patched_discovery(
        [DiscoveredDevice(ip=HOST, device_id=DEVICE_ID, unit_type=3)]
    ), patched_read_params(return_value=READ_PARAMS_OK):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": HOST}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"password": "1111"}
        )
        await hass.async_block_till_done()

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"
