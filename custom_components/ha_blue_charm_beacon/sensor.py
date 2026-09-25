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
        self._address = address.lower()
        self._attr_unique_id = f"{address}_battery"
        
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
            """Catch advertisements and parse Eddystone-TLM battery voltage."""
            if service_info.address.lower() == self._address:
                try:
                    for uuid, s_data in service_info.service_data.items():
                        if "feaa" in uuid.lower():
                            data_bytes = bytes.fromhex(s_data) if isinstance(s_data, str) else s_data
                            
                            # Eddystone-TLM layout: Bytes 2-3 contain big-endian voltage in mV
                            if len(data_bytes) >= 4:
                                voltage_mv = int.from_bytes(data_bytes[2:4], byteorder="big")
                                
                                if voltage_mv > 2000:
                                    if voltage_mv >= 3000:
                                        battery_pct = 100
                                    elif voltage_mv <= 2000:
                                        battery_pct = 0
                                    else:
                                        battery_pct = int((voltage_mv - 2000) / 10)

                                    if self._attr_native_value != battery_pct:
                                        self._attr_native_value = battery_pct
                                        self.async_write_ha_state()
                                        return
                except Exception as err:
                    _LOGGER.error("Error parsing Blue Charm TLM battery frame: %s", err, exc_info=True)

        self.async_on_remove(
            async_register_callback(
                self.hass,
                _handle_bluetooth,
                None,
                BluetoothScanningMode.ACTIVE,
            )
        )