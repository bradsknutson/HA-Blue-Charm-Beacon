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


def parse_blue_charm_advertisement(service_info):
    """Parse advertisement packets via coordinator."""
    # Extract Eddystone-TLM voltage as before
    for uuid, s_data in service_info.service_data.items():
        if "feaa" in uuid.lower():
            data_bytes = bytes.fromhex(s_data) if isinstance(s_data, str) else s_data
            if len(data_bytes) >= 4:
                voltage_mv = int.from_bytes(data_bytes[2:4], byteorder="big")
                if voltage_mv > 2000:
                    battery_pct = 100 if voltage_mv >= 3000 else int((voltage_mv - 2000) / 10)
                    return {"battery": battery_pct}
    return {}


def sensor_update_to_bluetooth_data_update(parsed_data: dict) -> PassiveBluetoothDataUpdate:
    """Map parsed data to Home Assistant Bluetooth entities."""
    return PassiveBluetoothDataUpdate(
        entity_data={
            PassiveBluetoothEntityKey("battery", "battery"): parsed_data.get("battery")
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