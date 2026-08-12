"""Provider implementations for HA Bin Collection."""

from __future__ import annotations

from typing import Protocol

from aiohttp import ClientSession

from ..const import PROVIDER_ACV, PROVIDER_MIJNAFVALWIJZER
from ..models import BinCollectionData
from .acv import AcvProvider
from .base import ProviderError
from .mijnafvalwijzer import MijnAfvalwijzerProvider


class WasteProvider(Protocol):
    """Contract each collector adapter implements."""

    async def async_validate_address(self) -> str:
        """Validate the configured address and return its display label."""

    async def async_fetch(self) -> BinCollectionData:
        """Return normalized collection and notice data."""


def get_provider(session: ClientSession, config: dict[str, str]) -> WasteProvider:
    """Create the provider selected by a config entry."""
    provider = config["provider"]
    if provider == PROVIDER_MIJNAFVALWIJZER:
        return MijnAfvalwijzerProvider(session, config)
    if provider == PROVIDER_ACV:
        return AcvProvider(session, config)
    raise ProviderError(f"Unsupported provider: {provider}")
