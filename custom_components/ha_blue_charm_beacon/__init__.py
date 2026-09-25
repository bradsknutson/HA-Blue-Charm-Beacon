from __future__ import annotations

import logging

from homeassistant.components.bluetooth import BluetoothScanningMode
from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothProcessorCoordinator,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


def parse_blue_charm_advertisement(service_info):
    """Parse advertisement packets via coordinator."""
    for uuid, s_data in service_info.service_data.items():
        if "feaa" in uuid.lower():
            data_bytes = bytes.fromhex(s_data) if isinstance(s_data, str) else s_data
            if len(data_bytes) >= 4:
                voltage_mv = int.from_bytes(data_bytes[2:4], byteorder="big")
                if voltage_mv > 2000:
                    battery_pct = 100 if voltage_mv >= 3000 else int((voltage_mv - 2000) / 10)
                    return {"battery": battery_pct}
    return {}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Blue Charm Beacon from a config entry."""
    address = entry.data["address"]
    
    # This core coordinator registers the device with Home Assistant's Bluetooth map & tables
    coordinator = PassiveBluetoothProcessorCoordinator(
        hass,
        _LOGGER,
        address=address,
        mode=BluetoothScanningMode.ACTIVE,
        update_method=parse_blue_charm_advertisement,
    )
    
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)