from __future__ import annotations

import logging

from homeassistant.components.bluetooth import (
    BluetoothChange,
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
    async_register_callback,
)
from homeassistant.components.device_tracker import SourceType, TrackerEntity
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
    """Set up Blue Charm beacon device tracker based on a config entry."""
    address = entry.data["address"]
    name = entry.data.get("name", "Blue Charm Beacon")
    async_add_entities([BlueCharmDeviceTracker(address, name)])


class BlueCharmDeviceTracker(TrackerEntity):
    """Representation of a Blue Charm Beacon Device Tracker."""

    _attr_has_entity_name = True
    _attr_name = None  
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, address: str, name: str) -> None:
        """Initialize the device tracker."""
        self._address = address.lower()
        self._attr_unique_id = f"{address}_tracker"
        self._attr_source_type = SourceType.BLUETOOTH
        self._attr_is_connected = False
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
            name=name,
            manufacturer="Blue Charm",
            model="BLE Beacon",
            connections={(CONNECTION_BLUETOOTH, address.lower())},
        )

    @property
    def state(self) -> str:
        """Return the state of the device tracker ('home' or 'not_home')."""
        return "home" if self._attr_is_connected else "not_home"

    async def async_added_to_hass(self) -> None:
        """Register callbacks when entity is added to hass."""
        await super().async_added_to_hass()

        @callback
        def _handle_bluetooth(
            service_info: BluetoothServiceInfoBleak, change: BluetoothChange
        ) -> None:
            """Mark as connected/home when a packet is heard from this MAC."""
            if service_info.address.lower() == self._address:
                if not self._attr_is_connected:
                    self._attr_is_connected = True
                    self.async_write_ha_state()

        self.async_on_remove(
            async_register_callback(
                self.hass,
                _handle_bluetooth,
                None,
                BluetoothScanningMode.ACTIVE,
            )
        )