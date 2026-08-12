"""ACV provider using the Ximmio public API."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

from aiohttp import ClientError, ClientSession, ClientTimeout

from ..const import ACV_COMPANY_CODE
from ..models import BinCollectionData
from .base import ProviderError, collection_from_item, notice_from_item, notice_is_active

BASE_URL = "https://api.ximmio.com/api"

_LOGGER = logging.getLogger(__name__)


class AcvProvider:
    """Fetch ACV collections for a resolved Ximmio household."""

    def __init__(self, session: ClientSession, config: dict[str, str]) -> None:
        self._session = session
        self._config = config
        self._address_id = config.get("address_id")

    async def async_get_addresses(self) -> list[dict[str, Any]]:
        params = {
            "companyCode": ACV_COMPANY_CODE,
            "postCode": self._config["postcode"],
            "houseNumber": self._config["house_number"],
            "houseLetter": self._config.get("addition", ""),
        }
        try:
            _LOGGER.debug("Requesting ACV address lookup")
            async with self._session.get(
                f"{BASE_URL}/GetAllAddress", params=params, timeout=ClientTimeout(total=20)
            ) as response:
                response.raise_for_status()
                payload: Any = await response.json(content_type=None)
        except (ClientError, TimeoutError, ValueError) as err:
            _LOGGER.error("ACV address request failed")
            raise ProviderError("ACV is tijdelijk niet bereikbaar") from err
        result = payload.get("dataList", payload.get("data", [])) if isinstance(payload, dict) else payload
        if not isinstance(result, list) or not result:
            raise ProviderError("Adres niet gevonden bij ACV")
        _LOGGER.debug("Received ACV address response with %d candidates", len(result))
        return [item for item in result if isinstance(item, dict)]

    async def async_validate_address(self) -> str:
        addresses = await self.async_get_addresses()
        if not self._address_id:
            self._address_id = str(addresses[0].get("UniqueAddressID") or addresses[0].get("uniqueAddressID") or "")
        if not self._address_id:
            raise ProviderError("ACV gaf geen geldig adres-ID terug")
        first = addresses[0]
        return str(
            first.get("Address") or first.get("address") or f"{self._config['postcode']} {self._config['house_number']}"
        )

    async def async_fetch(self) -> BinCollectionData:
        if not self._address_id:
            await self.async_validate_address()
        if not self._address_id:
            raise ProviderError("ACV gaf geen geldig adres-ID terug")
        params = {
            "companyCode": ACV_COMPANY_CODE,
            "uniqueAddressID": self._address_id,
            "startDate": date.today().isoformat(),
            "endDate": (date.today() + timedelta(days=366)).isoformat(),
        }
        try:
            _LOGGER.debug("Requesting ACV calendar from %s through %s", params["startDate"], params["endDate"])
            async with self._session.get(
                f"{BASE_URL}/GetCalendar", params=params, timeout=ClientTimeout(total=20)
            ) as response:
                response.raise_for_status()
                payload: Any = await response.json(content_type=None)
        except (ClientError, TimeoutError, ValueError) as err:
            _LOGGER.error("ACV calendar request failed")
            raise ProviderError("ACV-kalender is tijdelijk niet bereikbaar") from err
        data = payload.get("data", payload) if isinstance(payload, dict) else payload
        items = data.get("items", data.get("calendar", data.get("dataList", []))) if isinstance(data, dict) else data
        messages = data.get("notifications", data.get("messages", [])) if isinstance(data, dict) else []
        collections = tuple(filter(None, (collection_from_item(item) for item in items if isinstance(item, dict))))
        notices = tuple(
            filter(
                None,
                (
                    notice_from_item(item)
                    for item in messages
                    if isinstance(item, dict) and notice_is_active(item, date.today())
                ),
            )
        )
        _LOGGER.debug(
            "Received ACV calendar response with %d items and %d messages",
            len(items) if isinstance(items, list) else 0,
            len(messages) if isinstance(messages, list) else 0,
        )
        _LOGGER.debug("Parsed ACV response into %d collections and %d notices", len(collections), len(notices))
        return BinCollectionData(collections, notices)
