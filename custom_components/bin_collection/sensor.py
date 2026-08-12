"""Sensor entities for HA Bin Collection."""

from __future__ import annotations

from datetime import date

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CANONICAL_WASTE_TYPES, DOMAIN
from .coordinator import BinCollectionCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up all stable waste sensors for an entry."""
    coordinator: BinCollectionCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities(
        [OverviewSensor(coordinator), NotificationsSensor(coordinator)]
        + [WasteSensor(coordinator, waste) for waste in CANONICAL_WASTE_TYPES]
    )


class BinCollectionEntity(CoordinatorEntity[BinCollectionCoordinator]):
    """Base entity with a shared device."""

    _attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.config_entry.entry_id)},
            name="Bin Collection",
            manufacturer="HA Bin Collection",
        )


class WasteSensor(BinCollectionEntity, SensorEntity):
    """Date of the next collection for one canonical category."""

    _attr_device_class = SensorDeviceClass.DATE

    def __init__(self, coordinator: BinCollectionCoordinator, waste_type: str) -> None:
        super().__init__(coordinator)
        self._waste_type = waste_type
        self._attr_translation_key = waste_type
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{waste_type}"

    @property
    def native_value(self) -> date | None:
        dates = [item.date for item in self.coordinator.data.collections if item.waste_type == self._waste_type]
        return min(dates) if dates else None


class OverviewSensor(BinCollectionEntity, SensorEntity):
    """One stable card entry point containing all upcoming collections."""

    _attr_translation_key = "overview"

    def __init__(self, coordinator: BinCollectionCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_overview"

    @property
    def native_value(self) -> str:
        upcoming = sorted(self.coordinator.data.collections, key=lambda item: item.date)
        return upcoming[0].date.isoformat() if upcoming else "none"

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        return {
            "collections": [
                {"date": item.date.isoformat(), "type": item.waste_type, "source_type": item.source_type}
                for item in sorted(self.coordinator.data.collections, key=lambda item: (item.date, item.waste_type))
            ],
            "notices": [
                {"id": item.id, "title": item.title, "body": item.body} for item in self.coordinator.data.notices
            ],
        }


class NotificationsSensor(BinCollectionEntity, SensorEntity):
    """Number and details of active provider notices."""

    _attr_translation_key = "notifications"

    def __init__(self, coordinator: BinCollectionCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_notifications"

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.notices)

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        return {
            "notices": [
                {"id": item.id, "title": item.title, "body": item.body} for item in self.coordinator.data.notices
            ]
        }
