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
from .models import BinCollectionData, Notice


class DeliveryManager:
    """Deliver new notices and one reminder for each collection date."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, coordinator: BinCollectionCoordinator) -> None:
        self.hass = hass
        self.entry = entry
        self.coordinator = coordinator
        self._store = Store[dict[str, list[str]]](hass, 1, f"{DOMAIN}.{entry.entry_id}.delivery")
        self._notified: set[str] = set()
        self._acknowledged: set[str] = set()
        self._deleted: set[str] = set()
        self._reminded: set[str] = set()
        self._unsub_time = None

    async def async_load(self) -> None:
        data = await self._store.async_load() or {}
        self._notified = set(data.get("notified", []))
        self._acknowledged = set(data.get("acknowledged", []))
        self._deleted = set(data.get("deleted", []))
        self._reminded = set(data.get("reminded", []))

    async def _async_save(self) -> None:
        await self._store.async_save(
            {
                "notified": sorted(self._notified)[-500:],
                "acknowledged": sorted(self._acknowledged)[-500:],
                "deleted": sorted(self._deleted)[-500:],
                "reminded": sorted(self._reminded)[-500:],
            }
        )

    def is_deleted(self, notice: Notice) -> bool:
        """Return whether a notice was locally removed from the dashboard card."""
        return self._notice_fingerprint(notice) in self._deleted

    async def async_acknowledge_notice(self, fingerprint: str) -> None:
        """Record acknowledgement and dismiss its persistent notification."""
        self._acknowledged.add(fingerprint)
        self._notified.add(fingerprint)
        await self._async_save()
        await self._async_dismiss_notification(fingerprint)
        self.coordinator.async_update_listeners()

    async def async_delete_notice(self, fingerprint: str) -> None:
        """Locally hide a provider notice without changing provider data."""
        self._deleted.add(fingerprint)
        self._acknowledged.add(fingerprint)
        self._notified.add(fingerprint)
        await self._async_save()
        await self._async_dismiss_notification(fingerprint)
        self.coordinator.async_update_listeners()

    async def _async_dismiss_notification(self, fingerprint: str) -> None:
        """Dismiss the matching persistent notification when it exists."""
        await self.hass.services.async_call(
            "persistent_notification",
            "dismiss",
            {"notification_id": f"{DOMAIN}_{self.entry.entry_id}_notice_{fingerprint[:10]}"},
            blocking=True,
        )

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
        active = {self._notice_fingerprint(notice) for notice in data.notices}
        changed = False
        for state in (self._notified, self._acknowledged, self._deleted):
            before = len(state)
            state.intersection_update(active)
            changed |= len(state) != before
        for notice in data.notices:
            fingerprint = self._notice_fingerprint(notice)
            if fingerprint in self._notified or fingerprint in self._acknowledged:
                continue
            notification_id = f"{DOMAIN}_{self.entry.entry_id}_notice_{fingerprint[:10]}"
            persistent_notification.async_create(self.hass, notice.body, notice.title, notification_id)
            self.hass.bus.async_fire(
                EVENT_PROVIDER_NOTICE,
                {"entry_id": self.entry.entry_id, "title": notice.title, "body": notice.body},
            )
            self._notified.add(fingerprint)
            changed = True
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
        if fingerprint in self._reminded:
            return
        self._reminded.add(fingerprint)
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

    @classmethod
    def _notice_fingerprint(cls, notice: Notice) -> str:
        """Return the stable acknowledgement key for one provider notice."""
        return cls._fingerprint("notice", notice.id, notice.title, notice.body)
