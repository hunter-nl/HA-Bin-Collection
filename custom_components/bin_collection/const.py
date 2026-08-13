"""Constants for Bin Collection."""

from datetime import timedelta

DOMAIN = "bin_collection"
PLATFORMS = ["sensor", "calendar"]
CARD_RESOURCE_URL = "/ha_bin_collection/bin-collection-card.js?v=1.0.0-beta.7"

PROVIDER_MIJNAFVALWIJZER = "mijnafvalwijzer"
PROVIDER_ACV = "acv"
PROVIDER_LABELS = {
    PROVIDER_MIJNAFVALWIJZER: "MijnAfvalwijzer",
    PROVIDER_ACV: "ACV",
}
ACV_COMPANY_CODE = "f8e2844a-095e-48f9-9f98-71fceb51d2c3"

CONF_PROVIDER = "provider"
CONF_POSTCODE = "postcode"
CONF_HOUSE_NUMBER = "house_number"
CONF_ADDITION = "addition"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_REMINDER_ENABLED = "reminder_enabled"
CONF_REMINDER_TIME = "reminder_time"
CONF_LOG_LEVEL = "log_level"
CONF_DEVICE_NAME = "device_name"

DEFAULT_SCAN_INTERVAL = 6
DEFAULT_REMINDER_ENABLED = True
DEFAULT_REMINDER_TIME = "20:00:00"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_DEVICE_NAME = "Bin Collection"
DEFAULT_UPDATE_INTERVAL = timedelta(hours=DEFAULT_SCAN_INTERVAL)

EVENT_COLLECTION_REMINDER = f"{DOMAIN}.collection_reminder"
EVENT_PROVIDER_NOTICE = f"{DOMAIN}.provider_notice"
SERVICE_DELETE_NOTICE = "delete_notice"
CANONICAL_WASTE_TYPES = ("rest", "paper", "gft", "pmd")


def reminder_enabled_key(waste_type: str) -> str:
    """Return the option key for a waste-type reminder toggle."""
    return f"reminder_{waste_type}_enabled"


def reminder_time_key(waste_type: str) -> str:
    """Return the option key for a waste-type reminder time."""
    return f"reminder_{waste_type}_time"
