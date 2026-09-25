from __future__ import annotations

import logging

from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothDataProcessor,
    PassiveBluetoothDataUpdate,
    PassiveBluetoothEntityKey,
    PassiveBluetoothProcessorEntity,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def sensor_update_to_bluetooth_data_update(parsed_data: dict) -> PassiveBluetoothDataUpdate:
    """Map parsed data dictionary to Home Assistant Bluetooth entities."""
    return PassiveBluetoothDataUpdate(
        entity_data={
            PassiveBluetoothEntityKey("battery", None): parsed_data.get("battery")
        },
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Blue Charm beacon sensor using the coordinator processor."""
    coordinator = entry.runtime_data
    processor = PassiveBluetoothDataProcessor(sensor_update_to_bluetooth_data_update)
    
    entry.async_on_unload(processor.async_add_entities_listener(BlueCharmBatterySensor, async_add_entities))
    entry.async_on_unload(coordinator.async_register_processor(processor))


class BlueCharmBatterySensor(PassiveBluetoothProcessorEntity, SensorEntity):
    """Representation of a Blue Charm Beacon Battery Sensor via Bluetooth Coordinator."""

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "%"
    _attr_has_entity_name = True
    _attr_name = "Battery"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, processor: PassiveBluetoothDataProcessor, entity_key: PassiveBluetoothEntityKey) -> None:
        """Initialize the battery sensor."""
        super().__init__(processor, entity_key)
        address = self.coordinator.address
        name = self.coordinator.config_entry.data.get("name", "Blue Charm Beacon")
        
        self._attr_unique_id = f"{address}_battery"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
            name=name,
            manufacturer="Blue Charm",
            model="BLE Beacon",
            connections={(CONNECTION_BLUETOOTH, address.lower())},
        )