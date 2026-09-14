from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class BlueCharmConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Blue Charm Beacon."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            return self.async_create_entry(
                title=user_input["name"],
                data={
                    "address": user_input["address"],
                    "name": user_input["name"],
                },
            )

        # Get already configured addresses to exclude them
        current_addresses = {
            entry.data["address"] for entry in self._async_current_entries()
        }

        # Query discovered bluetooth advertisements from HA cache
        discovered_devices = bluetooth.async_discovered_service_info(self.hass)

        options = {}
        for discovery in discovered_devices:
            if discovery.address not in current_addresses:
                name = discovery.name or "Unknown Device"
                options[discovery.address] = f"{name} ({discovery.address})"

        if not options:
            options[""] = "No new Bluetooth devices detected"

        schema = vol.Schema(
            {
                vol.Required("name"): str,
                vol.Required("address"): vol.In(options),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
