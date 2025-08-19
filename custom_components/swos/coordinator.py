
from __future__ import annotations

from datetime import timedelta
from typing import Any, Dict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL
from .api import SwOSClient


class SwOSCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, client: SwOSClient, interval: int = DEFAULT_SCAN_INTERVAL) -> None:
        super().__init__(
            hass,
            logger=hass.helpers.logger.logging.getLogger(__name__),
            name="SwOS Coordinator",
            update_interval=timedelta(seconds=interval),
        )
        self.client = client

    async def _async_update_data(self) -> Dict[str, Any]:
        try:
            data = await self.client.fetch_all()
            if not data:
                raise UpdateFailed("No data from SwOS")
            return data
        except Exception as err:
            raise UpdateFailed(str(err)) from err
