"""Config flow for the Blauberg Vento integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from blauberg_vento import (
    AsyncVentoClient,
    DiscoveredDevice,
    Param,
    VentoAuthError,
    VentoError,
)

from .auth import ProbeAuthError, ProbeConnectionError, async_probe_credentials
from .const import (
    CONF_DEVICE_ID,
    CONF_HOST,
    CONF_PASSWORD,
    DEFAULT_DEVICE_ID,
    DEFAULT_PASSWORD,
    DISCOVERY_TIMEOUT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

MANUAL_ENTRY = "manual"

MANUAL_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PASSWORD, default=DEFAULT_PASSWORD): str,
    }
)

PASSWORD_SCHEMA = vol.Schema(
    {vol.Optional(CONF_PASSWORD, default=DEFAULT_PASSWORD): str}
)


async def async_validate_input(
    hass: HomeAssistant,
    host: str,
    password: str,
    device_id: str | None = None,
) -> dict[str, Any]:
    """Validate the credentials and return the device identity.

    Validation is two-stage, because the device does not authenticate requests
    addressed to DEFAULT_DEVICEID. Measured on a live unit:

        DEFAULT_DEVICEID + any password  -> FUNC 0x06 (accepted)
        <real device id> + bad password  -> FUNC 0x07 (rejected)

    A single read through DEFAULT_DEVICEID therefore proves only that some
    Vento unit is at this address; it says nothing about the password. Stage 1
    learns the real device ID unauthenticated, stage 2 re-probes with that ID
    so the password is actually tested before the entry is created.
    """
    if device_id is None:
        # Stage 1: learn the real device ID. This read is deliberately
        # unauthenticated, and proves only that a Vento unit is at this
        # address. The discovery path already knows the ID and skips it.
        anon = AsyncVentoClient(
            host=host, device_id=DEFAULT_DEVICE_ID, password=password
        )
        try:
            found = await anon.read_params([Param.DEVICE_SEARCH])
        except VentoError as err:
            raise CannotConnect from err
        device_id = found[Param.DEVICE_SEARCH].decode("ascii", errors="replace")
        if not device_id:
            raise CannotConnect

    # Stage 2: the only check that exercises the password. It has to run
    # before any authenticated library call, because the library reports the
    # device's FUNC 0x07 rejection as a generic protocol error, which would
    # otherwise be reported to the user as "cannot connect".
    try:
        await async_probe_credentials(host, device_id, password)
    except ProbeAuthError as err:
        raise InvalidAuth from err
    except ProbeConnectionError as err:
        raise CannotConnect from err

    # Stage 3: a full authenticated read, so the entry is only created once
    # the real client has talked to the real device.
    client = AsyncVentoClient(host=host, device_id=device_id, password=password)
    try:
        params = await client.read_params([Param.DEVICE_SEARCH, Param.UNIT_TYPE])
    except VentoAuthError as err:
        raise InvalidAuth from err
    except VentoError as err:
        raise CannotConnect from err

    read_device_id: str = params[Param.DEVICE_SEARCH].decode("ascii", errors="replace")
    if read_device_id != device_id:
        raise CannotConnect
    return {"device_id": read_device_id}


class BlaubergVentoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the Blauberg Vento config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the flow."""
        self._discovered_devices: list[DiscoveredDevice] = []
        self._selected_device: DiscoveredDevice | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step: discover or manual entry."""
        if user_input is not None:
            self._selected_device = None
            return await self._async_finish(
                user_input[CONF_HOST], user_input[CONF_PASSWORD]
            )

        try:
            self._discovered_devices = await AsyncVentoClient.discover(
                timeout=DISCOVERY_TIMEOUT
            )
        except VentoError:
            self._discovered_devices = []

        if self._discovered_devices:
            return await self.async_step_discovery()

        return self.async_show_form(
            step_id="user",
            data_schema=MANUAL_SCHEMA,
            errors={"base": "no_devices_found"},
        )

    async def async_step_discovery(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Let the user pick one of the discovered devices."""
        if user_input is not None:
            if user_input[CONF_HOST] == MANUAL_ENTRY:
                return self.async_show_form(step_id="user", data_schema=MANUAL_SCHEMA)
            self._selected_device = next(
                device
                for device in self._discovered_devices
                if device.ip == user_input[CONF_HOST]
            )
            return await self.async_step_credentials()

        options = {
            device.ip: f"{device.unit_type_name} ({device.ip})"
            for device in self._discovered_devices
        }
        options[MANUAL_ENTRY] = "Manually configure a device"
        return self.async_show_form(
            step_id="discovery",
            data_schema=vol.Schema({vol.Required(CONF_HOST): vol.In(options)}),
        )

    async def async_step_credentials(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Ask for the password of the selected discovered device."""
        if user_input is not None and self._selected_device is not None:
            return await self._async_finish(
                self._selected_device.ip, user_input[CONF_PASSWORD]
            )

        return self.async_show_form(step_id="credentials", data_schema=PASSWORD_SCHEMA)

    async def _async_finish(self, host: str, password: str) -> FlowResult:
        """Validate the connection and create the entry."""
        errors: dict[str, str] = {}
        device_id: str | None = None
        discovered_id = (
            self._selected_device.device_id if self._selected_device else None
        )

        try:
            validated = await async_validate_input(
                self.hass, host, password, discovered_id
            )
            device_id = validated["device_id"]
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except HomeAssistantError:
            errors["base"] = "cannot_connect"

        if device_id is None:
            _LOGGER.debug("Validation for %s failed: %s", host, errors)
            if self._selected_device is not None:
                return self.async_show_form(
                    step_id="credentials", data_schema=PASSWORD_SCHEMA, errors=errors
                )
            return self.async_show_form(
                step_id="user", data_schema=MANUAL_SCHEMA, errors=errors
            )

        await self.async_set_unique_id(device_id)
        self._abort_if_unique_id_configured({CONF_HOST: host, CONF_PASSWORD: password})

        return self.async_create_entry(
            title=device_id,
            data={
                CONF_HOST: host,
                CONF_PASSWORD: password,
                CONF_DEVICE_ID: device_id,
            },
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> FlowResult:
        """Start re-authentication after the device rejected the stored password."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Ask for a new password and verify it against the device."""
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await async_validate_input(
                    self.hass,
                    entry.data[CONF_HOST],
                    user_input[CONF_PASSWORD],
                    entry.data[CONF_DEVICE_ID],
                )
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except (CannotConnect, HomeAssistantError):
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(
                    entry, data_updates={CONF_PASSWORD: user_input[CONF_PASSWORD]}
                )

        return self.async_show_form(
            step_id="reauth_confirm", data_schema=PASSWORD_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Return the options flow handler (none for now)."""
        return BlaubergVentoOptionsFlow()


class BlaubergVentoOptionsFlow(config_entries.OptionsFlow):
    """Empty options flow."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options — nothing to configure yet."""
        return self.async_abort(reason="not_supported")


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
