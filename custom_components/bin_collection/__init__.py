"""Bin Collection integration setup."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from pathlib import Path
from typing import Any, cast

from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace.const import CONF_RESOURCE_TYPE_WS, LOVELACE_DATA
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .const import (
    CARD_RESOURCE_URL,
    CONF_LOG_LEVEL,
    DEFAULT_LOG_LEVEL,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import BinCollectionCoordinator
from .notifications import DeliveryManager

type BinCollectionConfigEntry = ConfigEntry[BinCollectionCoordinator]

_LOGGER = logging.getLogger(__package__)

_LOG_LEVELS = {"DEBUG": logging.DEBUG, "INFO": logging.INFO, "WARNING": logging.WARNING, "ERROR": logging.ERROR}

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup_entry(hass: HomeAssistant, entry: BinCollectionConfigEntry) -> bool:
    """Set up Bin Collection from one config entry."""
    log_level = _set_log_level(hass)
    _LOGGER.info("Setting up Bin Collection service (effective log level: %s)", log_level)
    hass.data.setdefault(DOMAIN, {})
    await _async_register_card_resource(hass)
    coordinator = BinCollectionCoordinator(hass, entry)
    delivery = DeliveryManager(hass, entry, coordinator)
    await delivery.async_load()
    coordinator.async_add_listener(delivery.async_handle_update)
    await coordinator.async_config_entry_first_refresh()
    delivery.async_schedule()
    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator, "delivery": delivery}
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    _LOGGER.info("Bin Collection service ready")
    return True


def effective_log_level(log_levels: Iterable[str]) -> str:
    """Return the most verbose valid integration log level."""
    return min(
        (level for level in log_levels if level in _LOG_LEVELS), key=_LOG_LEVELS.__getitem__, default=DEFAULT_LOG_LEVEL
    )


def _set_log_level(hass: HomeAssistant) -> str:
    """Apply the deterministic integration-wide log level."""
    log_level = effective_log_level(
        str(entry.options.get(CONF_LOG_LEVEL, DEFAULT_LOG_LEVEL)).upper()
        for entry in hass.config_entries.async_entries(DOMAIN)
    )
    _LOGGER.setLevel(_LOG_LEVELS[log_level])
    return log_level


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register the bundled Lovelace resource path once."""
    frontend_path = Path(__file__).parent / "frontend"
    await hass.http.async_register_static_paths(
        [StaticPathConfig("/ha_bin_collection", str(frontend_path), cache_headers=False)]
    )
    return True


async def _async_register_card_resource(hass: HomeAssistant) -> None:
    """Add the bundled card to Lovelace storage resources once.

    Integrations must not alter YAML-mode resources. Storage-mode dashboards are
    safe to update through Home Assistant's resource collection.
    """
    lovelace = hass.data.get(LOVELACE_DATA)
    if lovelace is None:
        return
    resources = cast(Any, lovelace.resources)
    existing = resources.async_items()
    if any(resource.get("url", "").split("?", 1)[0] == CARD_RESOURCE_URL.split("?", 1)[0] for resource in existing):
        return
    if not hasattr(resources, "async_create_item"):
        return
    await resources.async_create_item({"url": CARD_RESOURCE_URL, CONF_RESOURCE_TYPE_WS: "module"})


async def _async_update_listener(hass: HomeAssistant, entry: BinCollectionConfigEntry) -> None:
    """Reload an entry when polling or reminder options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: BinCollectionConfigEntry) -> bool:
    """Unload an Bin Collection config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        runtime = hass.data[DOMAIN].pop(entry.entry_id)
        await runtime["delivery"].async_unload()
        _LOGGER.info("Unloaded Bin Collection service")
    return unloaded
