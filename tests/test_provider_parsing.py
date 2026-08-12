"""Tests for provider-independent parsing helpers."""

from datetime import date

from custom_components.ha_bin_collection.providers.base import (
    collection_from_item,
    normalize_waste_type,
    notice_from_item,
)


def test_normalizes_required_categories_and_keeps_unknown_type() -> None:
    """Provider labels get stable entity categories without losing unknown values."""
    assert normalize_waste_type("Restafval") == "rest"
    assert normalize_waste_type("oud papier") == "paper"
    assert normalize_waste_type("Groente-Fruit-Tuinafval") == "gft"
    assert normalize_waste_type("Plastic verpakkingen") == "pmd"
    assert normalize_waste_type("Textiel afval") == "textiel_afval"


def test_parses_common_collection_and_notice_shapes() -> None:
    """Different provider field conventions yield the shared data model."""
    collection = collection_from_item({"pickupDate": "2026-12-24T00:00:00", "wasteType": "Papier"})
    notice = notice_from_item({"messageId": "rain", "subject": "Uitstel", "message": "Papier is vertraagd."})

    assert collection is not None
    assert collection.date == date(2026, 12, 24)
    assert collection.waste_type == "paper"
    assert notice is not None
    assert notice.id == "rain"
    assert notice.title == "Uitstel"
    assert notice.body == "Papier is vertraagd."
