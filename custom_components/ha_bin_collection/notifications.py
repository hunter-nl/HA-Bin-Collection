"""Persistent notification and automation-event delivery."""

from __future__ import annotations

from datetime import datetime, time, timedelta
from hashlib import sha256

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.storage import Store

from .const import (
    CONF_REMINDER_ENABLED,
    CONF_REMINDER_TIME,
    DEFAULT_REMINDER_ENABLED,
    DEFAULT_REMINDER_TIME,
    DOMAIN,
    EVENT_COLLECTION_REMINDER,
    EVENT_PROVIDER_NOTICE,
)
from .coordinator import BinCollectionCoordinator
from .models import BinCollectionData


class DeliveryManager:
    """Deliver new notices and one reminder for each collection date."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, coordinator: BinCollectionCoordinator) -> None:
        self.hass = hass
        self.entry = entry
        self.coordinator = coordinator
        self._store = Store[dict[str, list[str]]](hass, 1, f"{DOMAIN}.{entry.entry_id}.delivery")
        self._delivered: set[str] = set()
        self._unsub_time = None

    async def async_load(self) -> None:
        data = await self._store.async_load() or {}
        self._delivered = set(data.get("fingerprints", []))

    async def _async_save(self) -> None:
        await self._store.async_save({"fingerprints": sorted(self._delivered)[-500:]})

    def async_schedule(self) -> None:
        if self._unsub_time:
            self._unsub_time()
        if not self.entry.options.get(CONF_REMINDER_ENABLED, DEFAULT_REMINDER_ENABLED):
            return
        reminder_time = time.fromisoformat(self.entry.options.get(CONF_REMINDER_TIME, DEFAULT_REMINDER_TIME))
        self._unsub_time = async_track_time_change(
            self.hass, self._async_remind, hour=reminder_time.hour, minute=reminder_time.minute, second=0
        )

    async def async_unload(self) -> None:
        if self._unsub_time:
            self._unsub_time()
            self._unsub_time = None

    def async_handle_update(self) -> None:
        self.hass.async_create_task(self._async_handle_notices(self.coordinator.data))

    async def _async_handle_notices(self, data: BinCollectionData | None) -> None:
        if data is None:
            return
        changed = False
        for notice in data.notices:
            fingerprint = self._fingerprint("notice", notice.id, notice.title, notice.body)
            if fingerprint in self._delivered:
                continue
            changed = True
            self._delivered.add(fingerprint)
            notification_id = f"{DOMAIN}_{self.entry.entry_id}_notice_{fingerprint[:10]}"
            persistent_notification.async_create(self.hass, notice.body, notice.title, notification_id)
            self.hass.bus.async_fire(
                EVENT_PROVIDER_NOTICE,
                {"entry_id": self.entry.entry_id, "title": notice.title, "body": notice.body},
            )
        if changed:
            await self._async_save()

    async def _async_remind(self, now: datetime) -> None:
        data = self.coordinator.data
        if data is None:
            return
        target = (now + timedelta(days=1)).date()
        waste_types = sorted({item.waste_type for item in data.collections if item.date == target})
        if not waste_types:
            return
        fingerprint = self._fingerprint("reminder", target.isoformat(), ",".join(waste_types))
        if fingerprint in self._delivered:
            return
        self._delivered.add(fingerprint)
        labels = ", ".join(item.upper() for item in waste_types)
        message = f"Morgen ({target:%d-%m-%Y}) wordt opgehaald: {labels}."
        persistent_notification.async_create(
            self.hass, message, "Afvalherinnering", f"{DOMAIN}_{self.entry.entry_id}_reminder_{target.isoformat()}"
        )
        self.hass.bus.async_fire(
            EVENT_COLLECTION_REMINDER,
            {
                "entry_id": self.entry.entry_id,
                "date": target.isoformat(),
                "waste_types": waste_types,
                "message": message,
            },
        )
        await self._async_save()

    @staticmethod
    def _fingerprint(*parts: str) -> str:
        return sha256("\x1f".join(parts).encode()).hexdigest()
