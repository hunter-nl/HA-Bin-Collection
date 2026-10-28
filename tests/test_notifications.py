"""Tests for notification delivery helpers."""

from custom_components.bin_collection.notifications import _notification_title


def test_notification_title_identifies_collection_service() -> None:
    """A notification distinguishes the provider and configured address."""
    assert (
        _notification_title("MijnAfvalwijzer - 0000AA 0", "Gewijzigde inzameldag")
        == "MijnAfvalwijzer - 0000AA 0: Gewijzigde inzameldag"
    )
