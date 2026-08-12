"""HA Bin Collection integration setup."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace.const import CONF_RESOURCE_TYPE_WS, LOVELACE_DATA
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CARD_RESOURCE_URL, DOMAIN, PLATFORMS
from .coordinator import BinCollectionCoordinator
from .notifications import DeliveryManager

type BinCollectionConfigEntry = ConfigEntry[BinCollectionCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: BinCollectionConfigEntry) -> bool:
    """Set up HA Bin Collection from one config entry."""
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
    return True


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
    """Unload an HA Bin Collection config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        runtime = hass.data[DOMAIN].pop(entry.entry_id)
        await runtime["delivery"].async_unload()
    return unloaded
