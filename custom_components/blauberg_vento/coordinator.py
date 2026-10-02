"""Data update coordinator for the Blauberg Vento integration."""

from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from blauberg_vento import AsyncVentoClient, DeviceState, VentoError

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
            raise UpdateFailed(f"Error communicating with device: {err}") from err
