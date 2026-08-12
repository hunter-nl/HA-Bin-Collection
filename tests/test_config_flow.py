"""Tests for the configuration flow."""

from homeassistant.helpers import config_validation as cv
from voluptuous_serialize import convert

from custom_components.bin_collection.config_flow import address_schema, config_entry_title, normalize_postcode


def test_address_schema_is_serializable() -> None:
    """The frontend receives a serializable configuration schema."""
    schema = convert(address_schema(), custom_serializer=cv.custom_serializer)

    assert len(schema) == 4


def test_normalize_postcode_accepts_common_input() -> None:
    """Postcodes are stored in the provider-friendly format."""
    assert normalize_postcode("1234 ab") == "1234AB"


def test_config_entry_title_identifies_the_provider_and_address() -> None:
    """Each configured service has a distinct, recognizable title."""
    assert (
        config_entry_title({"provider": "mijnafvalwijzer", "postcode": "3962KE", "house_number": "25", "addition": ""})
        == "MijnAfvalwijzer - 3962KE 25"
    )
