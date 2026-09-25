from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN


class BlueCharmConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Blue Charm Beacon."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_device: BluetoothServiceInfoBleak | None = None
        self._discovered_devices: dict[str, str] = {}

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle the bluetooth discovery step."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        # Filter strictly for BCPro devices based on local name
        if not discovery_info.name or not discovery_info.name.startswith("BCPro_"):
            return self.async_abort(reason="not_supported")

        self._discovered_device = discovery_info
        self.context["title_placeholders"] = {"name": discovery_info.name}

        return await self.async_step_discovery_confirm()

    async def async_step_discovery_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm a discovered beacon."""
        assert self._discovered_device is not None

        if user_input is not None:
            return self.async_create_entry(
                title=self._discovered_device.name,
                data={
                    "name": self._discovered_device.name,
                    "address": self._discovered_device.address,
                },
            )

        return self.async_show_form(
            step_id="discovery_confirm",
            description_placeholders={
                "name": self._discovered_device.name,
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

        # Build a list of any currently broadcasting BCPro devices found nearby
        current_addresses = {entry.data.get("address") for entry in self._async_current_entries()}
        
        for discovery in async_discovered_service_info(self.hass):
            if discovery.address not in current_addresses and discovery.name and discovery.name.startswith("BCPro_"):
                self._discovered_devices[discovery.address] = f"{discovery.name} ({discovery.address})"

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