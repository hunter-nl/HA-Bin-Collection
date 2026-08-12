"""ACV provider using the Ximmio public API."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

from aiohttp import ClientError, ClientSession, ClientTimeout

from ..const import ACV_COMPANY_CODE
from ..models import BinCollectionData
from .base import ProviderError, collection_from_item, notice_from_item, notice_is_active

BASE_URL = "https://wasteapi.ximmio.com/api"

_LOGGER = logging.getLogger(__name__)


class AcvProvider:
    """Fetch ACV collections for a resolved Ximmio household."""

    def __init__(self, session: ClientSession, config: dict[str, str]) -> None:
        self._session = session
        self._config = config
        self._address_id = config.get("address_id")
        self._community = config.get("community")

    async def async_get_addresses(self) -> list[dict[str, Any]]:
        data = {
            "companyCode": ACV_COMPANY_CODE,
            "postCode": self._config["postcode"],
            "houseNumber": self._config["house_number"],
        }
        if addition := self._config.get("addition"):
            data["HouseLetter"] = addition
        try:
            _LOGGER.debug("Requesting ACV address lookup")
            async with self._session.post(
                f"{BASE_URL}/FetchAdress", data=data, timeout=ClientTimeout(total=20)
            ) as response:
                response.raise_for_status()
                payload: Any = await response.json(content_type=None)
        except (ClientError, TimeoutError, ValueError) as err:
            _LOGGER.error("ACV address request failed (%s)", type(err).__name__)
            raise ProviderError("ACV is tijdelijk niet bereikbaar") from err
        result = (
            payload.get("dataList", payload.get("datalist", payload.get("data", [])))
            if isinstance(payload, dict)
            else payload
        )
        if not isinstance(result, list) or not result:
            raise ProviderError("Adres niet gevonden bij ACV")
        _LOGGER.debug("Received ACV address response with %d candidates", len(result))
        return [item for item in result if isinstance(item, dict)]

    async def async_validate_address(self) -> str:
        addresses = await self.async_get_addresses()
        if not self._address_id:
            self._address_id = _address_id(addresses[0])
        if not self._address_id:
            raise ProviderError("ACV gaf geen geldig adres-ID terug")
        selected = next((item for item in addresses if _address_id(item) == self._address_id), addresses[0])
        self._community = str(selected.get("Community") or selected.get("community") or "") or None
        return str(
            selected.get("Address")
            or selected.get("address")
            or f"{self._config['postcode']} {self._config['house_number']}"
        )

    async def async_fetch(self) -> BinCollectionData:
        if not self._address_id or not self._community:
            await self.async_validate_address()
        if not self._address_id or not self._community:
            raise ProviderError("ACV gaf geen geldig adres-ID terug")
        data = {
            "companyCode": ACV_COMPANY_CODE,
            "uniqueAddressID": self._address_id,
            "community": self._community,
            "startDate": date.today().isoformat(),
            "endDate": (date.today() + timedelta(days=366)).isoformat(),
        }
        try:
            _LOGGER.debug("Requesting ACV calendar from %s through %s", data["startDate"], data["endDate"])
            async with self._session.post(
                f"{BASE_URL}/GetCalendar", data=data, timeout=ClientTimeout(total=20)
            ) as response:
                response.raise_for_status()
                payload: Any = await response.json(content_type=None)
        except (ClientError, TimeoutError, ValueError) as err:
            _LOGGER.error("ACV calendar request failed (%s)", type(err).__name__)
            raise ProviderError("ACV-kalender is tijdelijk niet bereikbaar") from err
        response_data = payload.get("data", payload) if isinstance(payload, dict) else payload
        items = (
            response_data.get("items", response_data.get("calendar", response_data.get("dataList", [])))
            if isinstance(response_data, dict)
            else response_data
        )
        messages = (
            response_data.get("notifications", response_data.get("messages", []))
            if isinstance(response_data, dict)
            else []
        )
        collections = tuple(_collections_from_items(items))
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


def _address_id(address: dict[str, Any]) -> str:
    """Return the address identifier used by current and older Ximmio responses."""
    return str(
        address.get("UniqueId")
        or address.get("uniqueId")
        or address.get("UniqueAddressID")
        or address.get("uniqueAddressID")
        or ""
    )


def _collections_from_items(items: object) -> list:
    """Normalize the current Ximmio pickupDates response and older item formats."""
    if not isinstance(items, list):
        return []
    collections = []
    for item in items:
        if not isinstance(item, dict):
            continue
        pickup_dates = item.get("pickupDates")
        source_type = item.get("_pickupTypeText")
        if isinstance(pickup_dates, list) and source_type:
            for pickup_date in pickup_dates:
                collection = collection_from_item({"pickupDate": pickup_date, "type": source_type})
                if collection:
                    collections.append(collection)
            continue
        collection = collection_from_item(item)
        if collection:
            collections.append(collection)
    return collections
