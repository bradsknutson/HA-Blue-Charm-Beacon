from __future__ import annotations

import logging

from homeassistant.components.bluetooth import (
    BluetoothChange,
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
    async_register_callback,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Blue Charm beacon sensor based on a config entry."""
    address = entry.data["address"]
    name = entry.data["name"]
    async_add_entities([BlueCharmBatterySensor(address, name)])


class BlueCharmBatterySensor(SensorEntity):
    """Representation of a Blue Charm Beacon Battery Sensor."""

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "%"
    _attr_has_entity_name = True
    _attr_name = "Battery"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, address: str, name: str) -> None:
        """Initialize the battery sensor."""
        self._address = address
        self._attr_unique_id = f"{address}_battery"
        
        # Link device to the integration domain and native bluetooth connection
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
            name=name,
            manufacturer="Blue Charm",
            model="BLE Beacon",
            connections={(CONNECTION_BLUETOOTH, address.lower())},
        )

    async def async_added_to_hass(self) -> None:
        """Register callbacks when entity is added to hass."""
        await super().async_added_to_hass()

        @callback
        def _handle_bluetooth(
            service_info: BluetoothServiceInfoBleak, change: BluetoothChange
        ) -> None:
            """Handle incoming Bluetooth advertisements and extract battery telemetry."""
            try:
                # Check manufacturer data payloads
                for m_id, m_data in service_info.manufacturer_data.items():
                    hex_str = m_data.hex()
                    # Look for BlueCharmBeacons signature to parse subsequent telemetry bytes
                    if "426c7565436861726d426561636f6e73" in hex_str:
                        # Blue Charm payload structure typically encodes voltage/battery indicators 
                        # after the string signature. Let's inspect the last few bytes or fallback safely.
                        # If a direct battery byte is present near the end or via TLM frames:
                        if len(m_data) >= 2:
                            # Example parsing: checking the last bytes or evaluating raw integers
                            potential_battery = m_data[-1]
                            if 0 <= potential_battery <= 100:
                                self._attr_native_value = potential_battery
                                self.async_write_ha_state()
                                return

                # Fallback: check service data for Eddystone-TLM (UUID feaa) if active on beacon
                for uuid, s_data in service_info.service_data.items():
                    if "feaa" in uuid.lower() and len(s_data) >= 14:
                        # Eddystone-TLM battery voltage is encoded in bytes 2 and 3 (in millivolts)
                        voltage = int.from_bytes(s_data[2:4], byteorder="big")
                        if voltage > 0:
                            # Approximate conversion from mV (e.g., 3000mV = 100%, 2000mV = 0%)
                            battery_pct = max(0, min(100, int((voltage - 2000) / 10)))
                            self._attr_native_value = battery_pct
                            self.async_write_ha_state()
                            return

            except Exception as err:
                _LOGGER.debug("Error parsing Blue Charm advertisement for battery: %s", err)

        self.async_on_remove(
            async_register_callback(
                self.hass,
                _handle_bluetooth,
                {"address": self._address.lower()},
                BluetoothScanningMode.ACTIVE,
            )
        )