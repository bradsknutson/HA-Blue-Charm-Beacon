from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

class BlueCharmConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HA Blue Charm Beacon."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            return self.async_create_entry(
                title=user_input.get("name", "Blue Charm Beacon"),
                data=user_input,
            )

        data_schema = vol.Schema(
            {
                vol.Required("name", default="Cat Beacon"): str,
                vol.Required("address"): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )
