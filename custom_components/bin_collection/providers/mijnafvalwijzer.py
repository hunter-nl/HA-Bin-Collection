"""MijnAfvalwijzer provider."""

from __future__ import annotations

from typing import Any

from aiohttp import ClientError, ClientSession, ClientTimeout

from ..models import BinCollectionData
from .base import ProviderError, collection_from_item, notice_from_item

URL = "https://api.mijnafvalwijzer.nl/webservices/appsinput/"
API_KEY = "5ef443e778f41c4f75c69459eea6e6ae0c2d92de729aa0fc61653815fbd6a8ca"


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
        try:
            async with self._session.get(URL, params=self._params(), timeout=ClientTimeout(total=20)) as response:
                response.raise_for_status()
                payload: dict[str, Any] = await response.json(content_type=None)
        except (ClientError, TimeoutError, ValueError) as err:
            raise ProviderError("MijnAfvalwijzer is tijdelijk niet bereikbaar") from err
        if payload.get("response") == "NOK":
            raise ProviderError(str(payload.get("error") or "Adres niet gevonden"))
        return payload

    async def async_validate_address(self) -> str:
        await self._async_request()
        return f"{self._config['postcode']} {self._config['house_number']}{self._config.get('addition', '')}"

    async def async_fetch(self) -> BinCollectionData:
        payload = await self._async_request()
        data = payload.get("data", payload)
        days = data.get("ophaaldagen", data.get("collections", data.get("data", []))) if isinstance(data, dict) else []
        messages = data.get("notifications", data.get("messages", [])) if isinstance(data, dict) else []
        collections = tuple(filter(None, (collection_from_item(item) for item in days if isinstance(item, dict))))
        notices = tuple(filter(None, (notice_from_item(item) for item in messages if isinstance(item, dict))))
        return BinCollectionData(collections, notices)
