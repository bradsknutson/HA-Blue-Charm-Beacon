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
    """Parse advertisement packets via coordinator and keep debug logging."""
    for uuid, s_data in service_info.service_data.items():
        if "feaa" in uuid.lower():
            data_bytes = bytes.fromhex(s_data) if isinstance(s_data, str) else s_data
            if len(data_bytes) >= 4:
                voltage_mv = int.from_bytes(data_bytes[2:4], byteorder="big")
                if voltage_mv > 2000:
                    if voltage_mv >= 3000:
                        battery_pct = 100
                    elif voltage_mv <= 2000:
                        battery_pct = 0
                    else:
                        battery_pct = int((voltage_mv - 2000) / 10)
                    
                    _LOGGER.error("COORDINATOR_PARSED_BATTERY: Computed %d%% from %d mV", battery_pct, voltage_mv)
                    return {"battery": battery_pct}
    return {}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Blue Charm Beacon from a config entry using the coordinator."""
    address = entry.data["address"]
    
    coordinator = PassiveBluetoothProcessorCoordinator(
        hass,
        _LOGGER,
        address=address,
        mode=BluetoothScanningMode.ACTIVE,
        update_method=parse_blue_charm_advertisement,
    )
    
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(coordinator.async_start())
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)