# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-09

### Added
- **E90-DTU (900SL30) Mountain Repeater Support**
  - Complete E90-DTU deployment guide (`E90_DTU_GUIDE.md`)
  - RS485 configuration script (`e90_repeater_setup.py`)
  - Finalization and lock script with remote config disable (`e90_finalize_and_lock.py`)
  - Configuration persistence test script (`e90_persistence_test.py`)
  - Lockout prevention guide (`E90_LOCKOUT_PREVENTION.md`)

- **Mountain Repeater Deployment**
  - Comprehensive deployment guide for 1500m altitude (`REPEATER_DEPLOYMENT.md`)
  - System architecture documentation (`README_SYSTEM.md`)
  - Solar power calculations and hardware recommendations
  - Line-of-sight range calculations
  - Weather protection and autonomous operation guidelines

- **LoRa Repeater Service**
  - MQTT-based LoRa repeater service (`lorarep.py`)
  - ChirpStack MQTT Forwarder integration
  - Safe dictionary/list access for robust operation
  - Updated to paho-mqtt API v2

- **Security Features**
  - RS485 physical disconnect procedure for remote config disable
  - AT+REMOLORA documentation and mitigation strategies
  - Configuration backup and restore system
  - Deployment checklists with security emphasis

### Fixed
- **E22 LoRa Module Configuration Bug**
  - Fixed `noise_enable` and `rssi_enable` overwriting same register bit
  - Separated to REG1 bit 5 (rssi_enable) and REG3 bit 7 (noise_enable)
  - File: `e22.py:96-109`

### Changed
- E90-DTU configuration uses CRYPT=0 (no encryption) for repeater compatibility
- Remote configuration security relies on RS485 physical disconnect
- All documentation in German for local deployment team

### Technical Details
- E90-DTU Channel 18 = 868.1 MHz (850.125 + 18)
- RELAY=RLYON enables automatic packet forwarding
- EEPROM persistence: >10 years retention, >100,000 write cycles
- 8-28V power input for direct solar connection
- 30 dBm (1W) transmit power for maximum range

### Deployment Context
- Dragino Gateway (ID: 48621185db7c38ca) at 700m altitude
- WireGuard VPN to heissa.de server in Kansas (130ms RTT)
- Mountain repeater planned for 1500m altitude, ~5km distance
- Expected ranges: SF7 (5-10km), SF12 (15-25km valley, 30-50km mountain-to-mountain)

[1.0.0]: https://github.com/gerontec/lora/releases/tag/v1.0.0
