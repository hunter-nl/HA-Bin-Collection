"""Config flow for Bin Collection."""

from __future__ import annotations

import re
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig, SelectSelectorMode

from .const import (
    CANONICAL_WASTE_TYPES,
    CONF_ADDITION,
    CONF_DEVICE_NAME,
    CONF_HOUSE_NUMBER,
    CONF_LOG_LEVEL,
    CONF_POSTCODE,
    CONF_PROVIDER,
    CONF_SCAN_INTERVAL,
    DEFAULT_DEVICE_NAME,
    DEFAULT_LOG_LEVEL,
    DEFAULT_REMINDER_TIME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PROVIDER_ACV,
    PROVIDER_LABELS,
    PROVIDER_MIJNAFVALWIJZER,
    reminder_enabled_key,
    reminder_time_key,
)
from .providers import ProviderError, get_provider
from .providers.acv import AcvProvider


def normalize_postcode(value: str) -> str:
    """Return a Dutch postcode in API-friendly form."""
    normalized = value.replace(" ", "").upper()
    if not re.fullmatch(r"\d{4}[A-Z]{2}", normalized):
        raise vol.Invalid("invalid_postcode")
    return normalized


def config_entry_title(config: dict[str, str]) -> str:
    """Return a distinct service title for one provider/address pair."""
    identifier = f"{config[CONF_POSTCODE]} {config[CONF_HOUSE_NUMBER]}{config.get(CONF_ADDITION, '')}"
    return f"{PROVIDER_LABELS[config[CONF_PROVIDER]]} - {identifier}"


def next_device_name(existing_names: set[str]) -> str:
    """Return the next available default device name."""
    if DEFAULT_DEVICE_NAME not in existing_names:
        return DEFAULT_DEVICE_NAME
    index = 2
    while f"{DEFAULT_DEVICE_NAME} {index}" in existing_names:
        index += 1
    return f"{DEFAULT_DEVICE_NAME} {index}"


def address_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Build the provider/address form schema."""
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_PROVIDER, default=defaults.get(CONF_PROVIDER, PROVIDER_MIJNAFVALWIJZER)): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        {"value": PROVIDER_MIJNAFVALWIJZER, "label": "MijnAfvalwijzer"},
                        {"value": PROVIDER_ACV, "label": "ACV"},
                    ],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(CONF_POSTCODE, default=defaults.get(CONF_POSTCODE, "")): str,
            vol.Required(CONF_HOUSE_NUMBER, default=defaults.get(CONF_HOUSE_NUMBER, "")): str,
            vol.Optional(CONF_ADDITION, default=defaults.get(CONF_ADDITION, "")): str,
        }
    )


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Set up one provider/address pair."""

    VERSION = 1

    _pending_input: dict[str, Any] | None = None
    _acv_addresses: dict[str, str] | None = None
    _acv_communities: dict[str, str] | None = None

    def _next_device_name(self) -> str:
        """Return a unique default name among configured Bin Collection services."""
        existing_names = {
            str(entry.data.get(CONF_DEVICE_NAME, DEFAULT_DEVICE_NAME))
            for entry in self.hass.config_entries.async_entries(DOMAIN)
        }
        return next_device_name(existing_names)

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Collect and validate the selected provider and address."""
        errors: dict[str, str] = {}
        if user_input is not None:
            user_input[CONF_ADDITION] = user_input.get(CONF_ADDITION, "").strip().upper()
            try:
                user_input[CONF_POSTCODE] = normalize_postcode(user_input[CONF_POSTCODE])
            except vol.Invalid:
                errors[CONF_POSTCODE] = "invalid_postcode"
            if not re.fullmatch(r"\d+", user_input[CONF_HOUSE_NUMBER]):
                errors[CONF_HOUSE_NUMBER] = "invalid_house_number"
            if not errors:
                try:
                    if user_input[CONF_PROVIDER] == PROVIDER_ACV:
                        addresses = await AcvProvider(
                            async_get_clientsession(self.hass), user_input
                        ).async_get_addresses()
                        choices = {
                            str(
                                item.get("UniqueId")
                                or item.get("uniqueId")
                                or item.get("UniqueAddressID")
                                or item.get("uniqueAddressID")
                            ): str(item.get("Address") or item.get("address") or user_input[CONF_POSTCODE])
                            for item in addresses
                            if item.get("UniqueId")
                            or item.get("uniqueId")
                            or item.get("UniqueAddressID")
                            or item.get("uniqueAddressID")
                        }
                        communities = {
                            str(
                                item.get("UniqueId")
                                or item.get("uniqueId")
                                or item.get("UniqueAddressID")
                                or item.get("uniqueAddressID")
                            ): str(item.get("Community") or item.get("community") or "")
                            for item in addresses
                            if item.get("UniqueId")
                            or item.get("uniqueId")
                            or item.get("UniqueAddressID")
                            or item.get("uniqueAddressID")
                        }
                        if len(choices) > 1:
                            self._pending_input = user_input
                            self._acv_addresses = choices
                            self._acv_communities = communities
                            return await self.async_step_acv_address()
                        if choices:
                            address_id = next(iter(choices))
                            user_input["address_id"] = address_id
                            if community := communities.get(address_id):
                                user_input["community"] = community
                    provider = get_provider(async_get_clientsession(self.hass), user_input)
                    await provider.async_validate_address()
                except ProviderError:
                    errors["base"] = "cannot_connect"
                else:
                    await self.async_set_unique_id(
                        "_".join(
                            (
                                user_input[CONF_PROVIDER],
                                user_input[CONF_POSTCODE],
                                user_input[CONF_HOUSE_NUMBER],
                                user_input[CONF_ADDITION],
                            )
                        )
                    )
                    self._abort_if_unique_id_configured()
                    user_input[CONF_DEVICE_NAME] = self._next_device_name()
                    return self.async_create_entry(title=config_entry_title(user_input), data=user_input)
        return self.async_show_form(step_id="user", data_schema=address_schema(user_input), errors=errors)

    async def async_step_acv_address(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Let the user choose when ACV returns more than one household address."""
        if self._pending_input is None or self._acv_addresses is None:
            return self.async_abort(reason="unknown")
        if user_input is not None:
            config = {**self._pending_input, "address_id": user_input["address_id"]}
            if community := (self._acv_communities or {}).get(user_input["address_id"]):
                config["community"] = community
            try:
                await get_provider(async_get_clientsession(self.hass), config).async_validate_address()
            except ProviderError:
                return self.async_show_form(
                    step_id="acv_address",
                    data_schema=vol.Schema({vol.Required("address_id"): vol.In(self._acv_addresses)}),
                    errors={"base": "cannot_connect"},
                )
            await self.async_set_unique_id(
                "_".join(
                    (config[CONF_PROVIDER], config[CONF_POSTCODE], config[CONF_HOUSE_NUMBER], config[CONF_ADDITION])
                )
            )
            self._abort_if_unique_id_configured()
            config[CONF_DEVICE_NAME] = self._next_device_name()
            return self.async_create_entry(title=config_entry_title(config), data=config)
        return self.async_show_form(
            step_id="acv_address", data_schema=vol.Schema({vol.Required("address_id"): vol.In(self._acv_addresses)})
        )

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> OptionsFlow:
        """Return the per-entry options flow."""
        return OptionsFlow()


class OptionsFlow(config_entries.OptionsFlow):
    """Configure polling and reminders."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Show reminder and refresh options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        options = self.config_entry.options
        fields: dict[object, object] = {
            vol.Required(CONF_SCAN_INTERVAL, default=options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=24)
            ),
            vol.Required(CONF_LOG_LEVEL, default=options.get(CONF_LOG_LEVEL, DEFAULT_LOG_LEVEL)): vol.In(
                ["DEBUG", "INFO", "WARNING", "ERROR"]
            ),
        }
        for waste_type in CANONICAL_WASTE_TYPES:
            fields[
                vol.Required(
                    reminder_enabled_key(waste_type), default=options.get(reminder_enabled_key(waste_type), True)
                )
            ] = bool
            fields[
                vol.Required(
                    reminder_time_key(waste_type),
                    default=options.get(reminder_time_key(waste_type), DEFAULT_REMINDER_TIME),
                )
            ] = str
        schema = vol.Schema(fields)
        return self.async_show_form(step_id="init", data_schema=schema)
