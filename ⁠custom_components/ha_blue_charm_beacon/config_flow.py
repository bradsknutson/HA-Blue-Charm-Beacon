from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import DOMAIN


class BlueCharmConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for HA Blue Charm Beacon."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial user step."""
        errors = {}

        if user_input is not None:
            address = user_input["address"].strip().upper()
            
            # Basic validation for MAC format length
            if len(address) != 17:
                errors["base"] = "invalid_mac"
            else:
                await self.async_set_unique_id(address)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=user_input["name"],
                    data={
                        "name": user_input["name"],
                        "address": address,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("name"): str,
                    vol.Required("address"): str,
                }
            ),
            errors=errors,
        )
