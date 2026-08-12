"""Calendar entity for all Bin Collection pickups."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BinCollectionCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the all-collections calendar."""
    async_add_entities([BinCollectionCalendar(hass.data[DOMAIN][entry.entry_id]["coordinator"])])


class BinCollectionCalendar(CoordinatorEntity[BinCollectionCoordinator], CalendarEntity):
    """Expose pickups as all-day calendar events."""

    _attr_has_entity_name = True
    _attr_translation_key = "calendar"

    def __init__(self, coordinator: BinCollectionCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_calendar"

    @property
    def event(self) -> CalendarEvent | None:
        upcoming = sorted(self.coordinator.data.collections, key=lambda item: item.date)
        if not upcoming:
            return None
        item = upcoming[0]
        return CalendarEvent(summary=item.source_type, start=item.date, end=item.date)

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        return [
            CalendarEvent(summary=item.source_type, start=item.date, end=item.date)
            for item in self.coordinator.data.collections
            if start_date.date() <= item.date <= end_date.date()
        ]
