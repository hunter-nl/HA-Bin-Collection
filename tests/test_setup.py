"""Tests for integration setup helpers."""

import asyncio
from types import SimpleNamespace
from typing import cast

from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.core import HomeAssistant

from custom_components.bin_collection import _async_register_card_resource


class _Resources:
    """Minimal Lovelace resource collection used to expose registration races."""

    def __init__(self) -> None:
        self.items: list[dict[str, str]] = []

    def async_items(self) -> list[dict[str, str]]:
        return list(self.items)

    async def async_create_item(self, item: dict[str, str]) -> None:
        await asyncio.sleep(0)
        self.items.append(item)


def test_card_resource_registration_is_serialized() -> None:
    """Concurrent config-entry setup creates one Lovelace resource."""
    resources = _Resources()
    hass = cast(
        HomeAssistant,
        SimpleNamespace(data={LOVELACE_DATA: SimpleNamespace(resources=resources)}),
    )

    async def register_concurrently() -> None:
        await asyncio.gather(
            _async_register_card_resource(hass),
            _async_register_card_resource(hass),
        )

    asyncio.run(register_concurrently())

    assert len(resources.items) == 1
    assert resources.items[0]["url"].startswith("/ha_bin_collection/bin-collection-card.js")
