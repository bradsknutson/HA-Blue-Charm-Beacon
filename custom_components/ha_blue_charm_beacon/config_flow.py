from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

# Hex-encoded byte signature for "BlueCharmBeacons" found in manufacturer data
BLUE_CHARM_SIGNATURE = "426c7565436861726d426561636f6e73"


class BlueCharmConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Blue Charm Beacon."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_device: BluetoothServiceInfoBleak | None = None
        self._discovered_devices: dict[str, str] = {}

    @staticmethod
    def _is_blue_charm(discovery_info: BluetoothServiceInfoBleak) -> bool:
        """Check if advertisement contains the Blue Charm byte signature."""
        for m_data in discovery_info.manufacturer_data.values():
            if BLUE_CHARM_SIGNATURE in m_data.hex():
                return True
        return False

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle the bluetooth discovery step using byte signature matching."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        # Filter strictly via the unique manufacturer byte signature
        if not self._is_blue_charm(discovery_info):
            return self.async_abort(reason="not_supported")

        self._discovered_device = discovery_info
        device_name = discovery_info.name or f"Blue Charm Beacon ({discovery_info.address})"
        self.context["title_placeholders"] = {"name": device_name}

        return await self.async_step_discovery_confirm()

    async def async_step_discovery_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm a discovered beacon."""
        assert self._discovered_device is not None

        if user_input is not None:
            name = user_input.get("name", self._discovered_device.name or "Blue Charm Beacon")
            return self.async_create_entry(
                title=name,
                data={
                    "name": name,
                    "address": self._discovered_device.address,
                },
            )

        return self.async_show_form(
            step_id="discovery_confirm",
            description_placeholders={
                "name": self._discovered_device.name or self._discovered_device.address,
                "address": self._discovered_device.address,
            },
        )

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial user-initiated step (manual configuration)."""
        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input["address"]
            await self.async_set_unique_id(address)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=user_input.get("name", "Blue Charm Beacon"),
                data=user_input,
            )

        # Build a list of any currently broadcasting Blue Charm devices found nearby using signature matching
        current_addresses = {entry.data.get("address") for entry in self._async_current_entries()}
        
        for discovery in async_discovered_service_info(self.hass):
            if discovery.address not in current_addresses and self._is_blue_charm(discovery):
                dev_name = discovery.name or "Blue Charm Beacon"
                self._discovered_devices[discovery.address] = f"{dev_name} ({discovery.address})"

        data_schema = vol.Schema(
            {
                vol.Required("name", default="Blue Charm Beacon"): str,
                vol.Required("address"): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )