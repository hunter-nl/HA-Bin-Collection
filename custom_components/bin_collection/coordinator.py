"""Coordinator for normalized waste collection data."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN
from .models import BinCollectionData
from .providers import ProviderError, get_provider

_LOGGER = logging.getLogger(__name__)


class BinCollectionCoordinator(DataUpdateCoordinator[BinCollectionData]):
    """Fetch one config entry on a configurable interval."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.config_entry = entry
        interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(hours=int(interval)),
        )

    async def _async_update_data(self) -> BinCollectionData:
        _LOGGER.info("Fetching collection data")
        provider = get_provider(async_get_clientsession(self.hass), dict(self.config_entry.data))
        try:
            data = await provider.async_fetch()
        except ProviderError as err:
            _LOGGER.error("Could not fetch collection data")
            raise UpdateFailed(str(err)) from err
        _LOGGER.info(
            "Received collection data: %d collections, %d notices",
            len(data.collections),
            len(data.notices),
        )
        if not data.collections:
            _LOGGER.warning("No collection dates were returned")
        return data
