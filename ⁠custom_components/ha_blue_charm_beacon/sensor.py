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
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
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

    def __init__(self, address: str, name: str) -> None:
        """Initialize the battery sensor."""
        self._address = address
        self._attr_unique_id = f"{address}_battery"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
            name=name,
            manufacturer="Blue Charm",
            connections={("bluetooth", address)},
        )

    async def async_added_to_hass(self) -> None:
        """Register callbacks when entity is added to hass."""
        await super().async_added_to_hass()

        @callback
        def _handle_bluetooth(
            service_info: BluetoothServiceInfoBleak, change: BluetoothChange
        ) -> None:
            """Handle incoming Bluetooth advertisements."""
            try:
                # Check manufacturer data payloads for battery attributes
                for m_id, m_data in service_info.manufacturer_data.items():
                    if len(m_data) > 0:
                        # Fallback parsing example matching broadcast metrics
                        battery_level = m_data[-1]
                        if 0 <= battery_level <= 100:
                            self._attr_native_value = battery_level
                            self.async_write_ha_state()
            except Exception:
                pass

        self.async_on_remove(
            async_register_callback(
                self.hass,
                _handle_bluetooth,
                {"address": self._address},
                BluetoothScanningMode.ACTIVE,
            )
        )
