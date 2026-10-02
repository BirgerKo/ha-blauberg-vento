# Blauberg Vento for Home Assistant

[![CI](https://github.com/BirgerKo/ha-blauberg-vento/actions/workflows/ci.yml/badge.svg)](https://github.com/BirgerKo/ha-blauberg-vento/actions/workflows/ci.yml)

A Home Assistant integration for [Blauberg Vento Expert Wi-Fi](https://blaubergventilatoren.de/) ventilation units, built on the [blauberg-vento](https://github.com/BirgerKo/blauberg_vento_api) Python library and communicating locally over the device's UDP protocol.

## Supported devices

- Vento Expert A50-1 / A85-1 / A100-1 W V.2
- Vento Expert Duo A30-1 W V.2
- Vento Expert A30 W V.2

## Features

- Automatic discovery of Vento devices on the local network, with manual IP fallback
- **Fan** control with the three standard speeds plus manual speed (0-255)
- **Operation mode** select: Ventilation, Heat recovery, Supply
- **Sensors**: humidity, fan RPM (both fans), filter countdown, machine hours, alarm status, firmware version
- **Binary sensors**: filter replacement indicator, relay input, boost mode
- **Numbers**: humidity threshold, boost delay, manual speed
- **Buttons**: reset filter timer, reset alarms
- **Switch**: weekly schedule
- 30-second local polling, no cloud connection required

## Installation

### HACS (recommended)

1. Add this repository to HACS as a custom repository (category: **Integration**).
2. Install **Blauberg Vento**.
3. Restart Home Assistant.

### Manual

Copy `custom_components/blauberg_vento/` to the `custom_components/` directory of your Home Assistant configuration and restart Home Assistant.

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **Blauberg Vento**.
3. Devices on your network are discovered automatically; pick one from the list or enter its IP address manually.
4. Enter the device password (default: `1111`).

Each Vento unit is added as a separate device, so multi-unit installations are fully supported.

## Development

```bash
pip install -r requirements_test.txt
pytest
ruff check custom_components tests
```

## License

MIT
