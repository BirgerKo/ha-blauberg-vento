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
    """Validate the credentials and return the device identity."""
    client = AsyncVentoClient(
        host=host, device_id=device_id or DEFAULT_DEVICE_ID, password=password
    )
    try:
        params = await client.read_params([Param.DEVICE_SEARCH, Param.UNIT_TYPE])
    except VentoAuthError as err:
        raise InvalidAuth from err
    except VentoError as err:
        raise CannotConnect from err

    read_device_id: str = params[Param.DEVICE_SEARCH].decode("ascii", errors="replace")
    if not read_device_id:
        raise CannotConnect
    if device_id is not None and read_device_id != device_id:
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
