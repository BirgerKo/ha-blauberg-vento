"""Data update coordinator for the Blauberg Vento integration."""

from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from blauberg_vento import AsyncVentoClient, DeviceState, VentoError

from .auth import ProbeAuthError, ProbeConnectionError, async_probe_credentials
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class VentoCoordinator(DataUpdateCoordinator[DeviceState]):
    """Coordinate state updates for a single Blauberg Vento device."""

    def __init__(self, hass: HomeAssistant, client: AsyncVentoClient) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.client = client

    async def _async_update_data(self) -> DeviceState:
        """Fetch the latest device state."""
        try:
            return await self.client.get_state()
        except VentoError as err:
            raise await self._classify(err) from err

    async def _classify(self, err: VentoError) -> Exception:
        """Decide whether a failed poll is an authentication or a network fault.

        The device answers a request that carries a wrong password with
        FUNC 0x07, which the library reports as a plain protocol error. Probe
        once on the failure path instead of matching on that message. A
        rejection means the password changed on the device, and the user must
        enter it again. Any other result is an unreachable device.
        """
        try:
            await async_probe_credentials(
                self.client.host, self.client.device_id, self.client.password
            )
        except ProbeAuthError:
            return ConfigEntryAuthFailed("The device rejected the stored password")
        except ProbeConnectionError:
            pass
        except Exception:  # noqa: BLE001 - diagnosis must not mask the real error
            _LOGGER.debug("Credential probe failed unexpectedly", exc_info=True)
        return UpdateFailed(f"Error communicating with device: {err}")
