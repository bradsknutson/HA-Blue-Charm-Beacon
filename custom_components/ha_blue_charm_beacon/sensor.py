from __future__ import annotations

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
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


def sensor_update_to_bluetooth_data_update(parsed_data: dict) -> PassiveBluetoothDataUpdate:
    """Map parsed data to Home Assistant Bluetooth entities."""
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

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        return self.processor.entity_data.get(self.entity_key)