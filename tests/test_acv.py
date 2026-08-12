"""Tests for the ACV Ximmio provider."""

import asyncio
from datetime import date
from typing import cast

from aiohttp import ClientSession

from custom_components.bin_collection.providers.acv import AcvProvider


class _Response:
    def __init__(self, payload: object) -> None:
        self.payload = payload

    async def __aenter__(self) -> _Response:
        return self

    async def __aexit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def raise_for_status(self) -> None:
        return None

    async def json(self, *, content_type: object) -> object:
        return self.payload


class _Session:
    def __init__(self, payloads: list[object]) -> None:
        self.payloads = iter(payloads)
        self.requests: list[tuple[str, dict[str, object]]] = []

    def post(self, url: str, *, data: dict[str, object], timeout: object) -> _Response:
        self.requests.append((url, data))
        return _Response(next(self.payloads))


def test_acv_uses_current_ximmio_post_endpoints() -> None:
    """ACV uses the current Ximmio address and calendar APIs."""
    asyncio.run(_test_acv_uses_current_ximmio_post_endpoints())


async def _test_acv_uses_current_ximmio_post_endpoints() -> None:
    """Exercise the asynchronous provider calls."""
    session = _Session(
        [
            {"dataList": [{"UniqueId": "address-1", "Community": "ACV", "Address": "Example"}]},
            {"dataList": [{"_pickupTypeText": "GFT", "pickupDates": ["2026-08-14T00:00:00"]}]},
        ]
    )
    provider = AcvProvider(cast(ClientSession, session), {"postcode": "1234AB", "house_number": "1", "addition": "A"})

    await provider.async_validate_address()
    data = await provider.async_fetch()

    assert session.requests[0] == (
        "https://wasteapi.ximmio.com/api/FetchAdress",
        {
            "companyCode": "f8e2844a-095e-48f9-9f98-71fceb51d2c3",
            "postCode": "1234AB",
            "houseNumber": "1",
            "HouseLetter": "A",
        },
    )
    assert session.requests[1][0] == "https://wasteapi.ximmio.com/api/GetCalendar"
    assert session.requests[1][1]["uniqueAddressID"] == "address-1"
    assert session.requests[1][1]["community"] == "ACV"
    assert data.collections[0].date == date(2026, 8, 14)
    assert data.collections[0].waste_type == "gft"
