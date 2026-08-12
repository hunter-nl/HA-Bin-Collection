"""Save a redacted MijnAfvalwijzer response for local provider investigation."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from aiohttp import ClientSession, ClientTimeout

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from custom_components.bin_collection.providers.mijnafvalwijzer import API_KEY, URL

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
)


def redacted_payload(payload: object, sensitive_values: set[str]) -> object:
    """Return a payload with household data and credentials redacted."""

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


async def async_main(args: argparse.Namespace) -> None:
    """Fetch one response and save its redacted JSON without logging it."""
    config = {
        "postcode": args.postcode.replace(" ", "").upper(),
        "house_number": args.house_number,
        "addition": args.addition.strip().upper(),
    }
    params = {
        "apikey": API_KEY,
        "method": "postcodecheck",
        "postcode": config["postcode"],
        "street": "",
        "huisnummer": config["house_number"],
        "toevoeging": config["addition"],
        "app_name": "afvalwijzer",
        "platform": "web",
        "langs": "nl",
    }
    async with ClientSession() as session, session.get(URL, params=params, timeout=ClientTimeout(total=20)) as response:
        response.raise_for_status()
        payload: Any = await response.json(content_type=None)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            redacted_payload(payload, {value for value in config.values() if value}), ensure_ascii=False, indent=2
        ),
        encoding="utf-8",
    )
    output.chmod(0o600)
    print(f"Saved redacted response to {output}")


def parse_args() -> argparse.Namespace:
    """Parse the household and output location without echoing them."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--postcode", required=True)
    parser.add_argument("--house-number", required=True)
    parser.add_argument("--addition", default="")
    parser.add_argument("--output", default="mijnafvalwijzer-response.redacted.json")
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(async_main(parse_args()))
