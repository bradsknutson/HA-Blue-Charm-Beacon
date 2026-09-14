# HA Blue Charm Beacon

A custom Home Assistant integration designed to discover Blue Charm Bluetooth Low Energy (BLE) beacons, register them as first-class hardware devices, and expose their battery levels directly through Home Assistant's native Bluetooth subsystem.

## Features

* **Native Device Registry:** Automatically binds beacons to physical MAC addresses so they display correctly on the Home Assistant Bluetooth map.
* **Direct Advertisement Tracking:** Listens to local adapters and remote ESP32 proxies via Home Assistant's central bluetooth bus without needing complex template workarounds.
* **Battery Sensors:** Spawns a dedicated battery percentage sensor entity for each configured beacon.

## Installation (HACS)

1. Ensure [HACS](https://hacs.xyz/) is installed in your Home Assistant instance.
2. Open HACS and navigate to **Integrations**.
3. Click the three dots in the top right corner and select **Custom repositories**.
4. Add the URL of this GitHub repository, select **Integration** as the category, and click **Add**.
5. Find **HA Blue Charm Beacon** in HACS, click **Download**, and restart Home Assistant.

## Manual Installation

1. Download or clone this repository.
2. Copy the `ha_blue_charm_beacon` directory into your Home Assistant `/config/custom_components/` folder.
3. Restart Home Assistant.

## Configuration

1. Go to **Settings > Devices & Services > Add Integration**.
2. Search for **HA Blue Charm Beacon**.
3. Enter a friendly name (e.g., `Cat 1 Tracker`) and the beacon's Bluetooth MAC address.
