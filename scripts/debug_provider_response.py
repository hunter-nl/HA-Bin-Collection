"""Save redacted raw provider responses for local troubleshooting."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from aiohttp import ClientSession, ClientTimeout

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from custom_components.bin_collection.const import ACV_COMPANY_CODE, PROVIDER_LABELS
from custom_components.bin_collection.providers.acv import BASE_URL as ACV_URL
from custom_components.bin_collection.providers.mijnafvalwijzer import API_KEY
from custom_components.bin_collection.providers.mijnafvalwijzer import URL as MIJNAFVALWIJZER_URL

_SENSITIVE_KEY_PARTS = (
    "address",
    "apikey",
    "api_key",
    "authorization",
    "email",
    "house",
    "password",
    "postcode",
    "post_code",
    "secret",
    "street",
    "token",
    "uniqueid",
    "unique_id",
)


def redacted_payload(payload: object, sensitive_values: set[str]) -> object:
    """Return a payload with credentials and household data redacted."""

    def redact(value: object, key: str = "") -> object:
        normalized_key = key.lower().replace("-", "_")
        if any(part in normalized_key for part in _SENSITIVE_KEY_PARTS):
            return "***"
        if isinstance(value, dict):
            return {str(child_key): redact(child_value, str(child_key)) for child_key, child_value in value.items()}
        if isinstance(value, list):
            return [redact(item) for item in value]
        if isinstance(value, str):
            for sensitive_value in sensitive_values:
                value = value.replace(sensitive_value, "***")
        return value

    return redact(payload)


async def _json_response(session: ClientSession, method: str, url: str, data: dict[str, str]) -> Any:
    """Fetch a JSON response without using Home Assistant logging."""
    if method == "POST":
        async with session.post(url, data=data, timeout=ClientTimeout(total=20)) as response:
            response.raise_for_status()
            return await response.json(content_type=None)
    async with session.get(url, params=data, timeout=ClientTimeout(total=20)) as response:
        response.raise_for_status()
        return await response.json(content_type=None)


def _address_items(payload: object) -> list[dict[str, Any]]:
    """Extract the current Ximmio address list."""
    if not isinstance(payload, dict):
        return []
    items = payload.get("dataList", payload.get("datalist", payload.get("data", [])))
    return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []


async def _mijnafvalwijzer_response(session: ClientSession, config: dict[str, str]) -> dict[str, Any]:
    """Collect the raw MijnAfvalwijzer response."""
    response = await _json_response(
        session,
        "GET",
        MIJNAFVALWIJZER_URL,
        {
            "apikey": API_KEY,
            "method": "postcodecheck",
            "postcode": config["postcode"],
            "street": "",
            "huisnummer": config["house_number"],
            "toevoeging": config["addition"],
            "app_name": "afvalwijzer",
            "platform": "web",
            "langs": "nl",
        },
    )
    return {"provider": "mijnafvalwijzer", "responses": {"calendar": response}}


async def _acv_response(session: ClientSession, config: dict[str, str]) -> dict[str, Any]:
    """Collect the raw Ximmio address and calendar responses used by ACV."""
    address_data = {
        "companyCode": ACV_COMPANY_CODE,
        "postCode": config["postcode"],
        "houseNumber": config["house_number"],
    }
    if config["addition"]:
        address_data["HouseLetter"] = config["addition"]
    address_response = await _json_response(session, "POST", f"{ACV_URL}/FetchAdress", address_data)
    addresses = _address_items(address_response)
    if not addresses:
        return {"provider": "acv", "responses": {"address": address_response}}
    address = addresses[0]
    address_id = str(
        address.get("UniqueId")
        or address.get("uniqueId")
        or address.get("UniqueAddressID")
        or address.get("uniqueAddressID")
        or ""
    )
    community = str(address.get("Community") or address.get("community") or "")
    if not address_id or not community:
        return {"provider": "acv", "responses": {"address": address_response}}
    calendar_response = await _json_response(
        session,
        "POST",
        f"{ACV_URL}/GetCalendar",
        {
            "companyCode": ACV_COMPANY_CODE,
            "uniqueAddressID": address_id,
            "community": community,
            "startDate": date.today().isoformat(),
            "endDate": (date.today() + timedelta(days=366)).isoformat(),
        },
    )
    return {"provider": "acv", "responses": {"address": address_response, "calendar": calendar_response}}


async def async_main(args: argparse.Namespace) -> None:
    """Fetch and save raw responses with sensitive values redacted."""
    config = {
        "postcode": args.postcode.replace(" ", "").upper(),
        "house_number": args.house_number,
        "addition": args.addition.strip().upper(),
    }
    async with ClientSession() as session:
        if args.provider == "mijnafvalwijzer":
            payload = await _mijnafvalwijzer_response(session, config)
        elif args.provider == "acv":
            payload = await _acv_response(session, config)
        else:
            raise ValueError(f"Provider diagnostics are not implemented for: {args.provider}")
    output = Path(args.output or f"{args.provider}-response.redacted.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            redacted_payload(payload, {value for value in config.values() if value} | {API_KEY}),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    output.chmod(0o600)
    print(f"Saved redacted {args.provider} response to {output}")


def parse_args() -> argparse.Namespace:
    """Parse provider, household, and output arguments without echoing them."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", required=True, choices=sorted(PROVIDER_LABELS))
    parser.add_argument("--postcode", required=True)
    parser.add_argument("--house-number", required=True)
    parser.add_argument("--addition", default="")
    parser.add_argument("--output")
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(async_main(parse_args()))
