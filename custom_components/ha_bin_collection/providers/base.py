"""Shared parsing helpers for waste collector providers."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from ..models import Collection, Notice


class ProviderError(Exception):
    """Raised when a collector cannot provide usable data."""


CATEGORY_ALIASES = {
    "rest": "rest",
    "restafval": "rest",
    "household waste": "rest",
    "papier": "paper",
    "paper": "paper",
    "oud papier": "paper",
    "gft": "gft",
    "groente fruit tuinafval": "gft",
    "organic": "gft",
    "pmd": "pmd",
    "plastic": "pmd",
    "plastic verpakkingen": "pmd",
    "plastic metal drinkkartons": "pmd",
}


def normalize_waste_type(value: object) -> str:
    """Map provider labels to stable, safe category identifiers."""
    label = " ".join(str(value or "").lower().replace("_", " ").replace("-", " ").split())
    if label in CATEGORY_ALIASES:
        return CATEGORY_ALIASES[label]
    return "".join(char if char.isalnum() else "_" for char in label).strip("_") or "other"


def parse_date(value: object) -> date | None:
    """Parse common provider date representations."""
    if not value:
        return None
    text = str(value).split("T", maxsplit=1)[0]
    for formatter in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, formatter).date()
        except ValueError:
            pass
    return None


def collection_from_item(item: dict[str, Any]) -> Collection | None:
    """Extract a collection from the common field names used by both APIs."""
    pickup_date = parse_date(item.get("date") or item.get("pickupDate") or item.get("dateTime"))
    source_type = item.get("type") or item.get("description") or item.get("wasteType") or item.get("name")
    if pickup_date is None or not source_type:
        return None
    return Collection(pickup_date, normalize_waste_type(source_type), str(source_type))


def notice_from_item(item: dict[str, Any]) -> Notice | None:
    """Extract a provider message without depending on provider-specific IDs."""
    title = str(item.get("title") or item.get("subject") or item.get("header") or "Afvalmelding").strip()
    body = str(item.get("body") or item.get("message") or item.get("content") or item.get("text") or "").strip()
    if not body:
        return None
    notice_id = str(item.get("id") or item.get("messageId") or f"{title}:{body}")
    return Notice(notice_id, title, body)
