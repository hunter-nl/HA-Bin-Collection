"""MijnAfvalwijzer provider."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

from aiohttp import ClientError, ClientSession, ClientTimeout

from ..models import BinCollectionData
from .base import ProviderError, collection_from_item, notice_from_item

URL = "https://api.mijnafvalwijzer.nl/webservices/appsinput/"
API_KEY = "5ef443e778f41c4f75c69459eea6e6ae0c2d92de729aa0fc61653815fbd6a8ca"

_LOGGER = logging.getLogger(__name__)


def response_items(response: object) -> list[dict[str, Any]]:
    """Extract list items from a MijnAfvalwijzer response section."""
    if isinstance(response, list):
        return [item for item in response if isinstance(item, dict)]
    if not isinstance(response, dict):
        return []
    items = response.get("data", [])
    return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def active_notice_items(items: list[dict[str, Any]], today: date) -> list[dict[str, Any]]:
    """Return notices that have not expired or aged past the pickup warning window."""
    active: list[dict[str, Any]] = []
    for item in items:
        expiry = item.get("expiration_date")
        published = item.get("date")
        if expiry:
            try:
                expiry_date = date.fromisoformat(str(expiry).split(" ", maxsplit=1)[0])
            except ValueError:
                expiry_date = None
            if expiry_date is not None and expiry_date < today:
                continue
        elif published:
            try:
                published_date = date.fromisoformat(str(published).split(" ", maxsplit=1)[0])
            except ValueError:
                published_date = None
            if published_date is not None and published_date < today - timedelta(days=1):
                continue
        active.append(item)
    return active


class MijnAfvalwijzerProvider:
    """Fetch the MijnAfvalwijzer calendar for one household."""

    def __init__(self, session: ClientSession, config: dict[str, str]) -> None:
        self._session = session
        self._config = config

    def _params(self) -> dict[str, str]:
        return {
            "apikey": API_KEY,
            "method": "postcodecheck",
            "postcode": self._config["postcode"],
            "street": "",
            "huisnummer": self._config["house_number"],
            "toevoeging": self._config.get("addition", ""),
            "app_name": "afvalwijzer",
            "platform": "web",
            "langs": "nl",
        }

    async def _async_request(self) -> dict[str, Any]:
        params = self._params()
        _LOGGER.debug("Requesting MijnAfvalwijzer data")
        try:
            async with self._session.get(URL, params=params, timeout=ClientTimeout(total=20)) as response:
                response.raise_for_status()
                payload: dict[str, Any] = await response.json(content_type=None)
        except (ClientError, TimeoutError, ValueError) as err:
            _LOGGER.error("MijnAfvalwijzer request failed")
            raise ProviderError("MijnAfvalwijzer is tijdelijk niet bereikbaar") from err
        raw_data = payload.get("data", {})
        if isinstance(raw_data, dict):
            _LOGGER.debug(
                "Received MijnAfvalwijzer response sections: %s",
                sorted(key for key in ("ophaaldagen", "mededelingen", "pushData", "notifications") if key in raw_data),
            )
        if payload.get("response") == "NOK":
            raise ProviderError(str(payload.get("error") or "Adres niet gevonden"))
        return payload

    async def async_validate_address(self) -> str:
        await self._async_request()
        return f"{self._config['postcode']} {self._config['house_number']}{self._config.get('addition', '')}"

    async def async_fetch(self) -> BinCollectionData:
        payload = await self._async_request()
        data = payload.get("data", payload)
        if not isinstance(data, dict):
            return BinCollectionData((), ())
        days = response_items(data.get("ophaaldagen", data.get("collections", data.get("data", []))))
        messages = [
            item
            for section in (data.get("mededelingen"), data.get("pushData"), data.get("notifications"))
            for item in response_items(section)
        ]
        collections = tuple(
            collection
            for item in days
            if (collection := collection_from_item(item)) is not None and collection.date >= date.today()
        )
        notices = tuple(filter(None, (notice_from_item(item) for item in active_notice_items(messages, date.today()))))
        _LOGGER.debug(
            "Parsed MijnAfvalwijzer response into %d collections and %d notices", len(collections), len(notices)
        )
        return BinCollectionData(collections, notices)
