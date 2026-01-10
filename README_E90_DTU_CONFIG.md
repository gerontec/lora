# E90-DTU Configuration Reader

Scripts to read the current configuration from E90-DTU(433C33) wireless modem.

## Overview

The E90-DTU(433C33) is a 433MHz wireless data transceiver that supports:
- RS232/RS485 interfaces
- Modbus protocol
- Continuous transmission (unlimited packet length)
- Up to 4km communication distance
- 10-28V power supply

## Hardware Setup

### 1. Set Device to Configuration Mode

**IMPORTANT:** The device must be in **Mode 2 (Command Mode)** to read configuration.

Set the DIP switch:
- **M1 = OFF** (switch down)
- **M0 = ON** (switch up)

```
DIP Switch Position for Mode 2:
┌─────┬─────┐
│  1  │  2  │
│ OFF │ ON  │
└─────┴─────┘
  M1    M0
```

### 2. Connect to Computer

- **Option A:** USB to RS232 converter → Connect to DB-9 port
- **Option B:** USB to RS485 converter → Connect to 485_A and 485_B terminals

### 3. Power the Device

- Use DC power adapter (12V or 24V recommended), OR
- Use VCC/GND terminals (10-28V DC)

### 4. Attach Antenna

**CRITICAL:** Always connect a 50Ω antenna before powering on to avoid damage!

## Usage

### Method 1: AT Commands (Recommended)

```bash
# Basic usage
python3 e90_dtu_config_reader.py

# Specify serial port
python3 e90_dtu_config_reader.py --port /dev/ttyUSB0

# Change baudrate (if device is configured differently)
python3 e90_dtu_config_reader.py --baud 115200

# Full options
python3 e90_dtu_config_reader.py --port /dev/ttyUSB0 --baud 9600 --timeout 2
```

### Method 2: Binary Protocol

If AT commands don't work, try the binary protocol version:

```bash
python3 e90_dtu_config_reader_binary.py --port /dev/ttyUSB0
```

## Expected Output

```
==============================================================
E90-DTU(433C33) Configuration Reader
==============================================================

[1/4] Testing communication...
→ Sent: AT
← Received: OK
✓ Device responding

[2/4] Reading device version...
→ Sent: AT+VER
← Received: AT+VER=E90-DTU(433C33) V1.5

[3/4] Reading LoRa configuration...
→ Sent: AT+LORA
← Received: AT+LORA=0,0,9600,240,RSCHOFF,PWMAX,80,RSDATOFF,TRNOR,RLYOFF,LBTOFF,WOROFF,500,0

[4/4] Reading UART configuration...
→ Sent: AT+UART
← Received: AT+UART=9600,8N1

==============================================================
CONFIGURATION SUMMARY
==============================================================

📋 Device Version:
   AT+VER=E90-DTU(433C33) V1.5

🔌 UART Configuration:
   AT+UART=9600,8N1

📡 LoRa Configuration:
   Station Address:     0
   Network ID:          0
   Channel:             80
   Frequency:           433.0 MHz
   Air Baudrate:        9600 bps
   Packet Length:       240 bytes
   TX Power:            2W (33dBm)
   Transfer Mode:       Transparent transmission
   RSSI Ambient:        RSCHOFF
   RSSI Data:           RSDATOFF
   Relay:               RLYOFF
   LBT:                 LBTOFF
   WOR Mode:            WOROFF
   WOR Timing:          500 ms
   Encryption:          0

==============================================================
```

## Configuration Parameters

### Station Address (0-65535)
- Devices with the same address can communicate
- Default: 0

### Network ID (0-255)
- Additional grouping parameter
- Default: 0

### Channel (0-255)
- Frequency = 425.0 MHz + (Channel × 0.1 MHz)
- Channel spacing: 100 kHz
- Frequency range: 425-450.5 MHz
- Default: 80 (433.0 MHz)

### TX Power
- PWMAX: 2W (33dBm) - Maximum range
- PWMID: 1W (30dBm)
- PWLOW: 0.5W (27dBm)
- PWMIN: 0.1W (20dBm)

### Transfer Mode
- TRNOR: Transparent transmission (default)
- TRFIX: Fixed-point transmission

### Air Baudrate
- Options: 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200
- Auto-adjusts to match UART baudrate
- Default: Matches UART (9600)

## Troubleshooting

### No Response from Device

1. **Check Mode Switch**
   - Ensure M1=OFF, M0=ON for configuration mode
   - Power cycle after changing switch

2. **Check Serial Port**
   ```bash
   # List available serial ports
   ls -l /dev/ttyUSB*
   ls -l /dev/ttyACM*

   # Check port permissions
   sudo chmod 666 /dev/ttyUSB0
   ```

3. **Check Baudrate**
   - Default is 9600 bps
   - If changed, use `--baud` option

4. **Check Connection**
   - RS232: Use null modem if needed
   - RS485: Check A/B polarity

### Permission Denied Error

```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Or change port permissions
sudo chmod 666 /dev/ttyUSB0
```

### Device Not Responding

1. Check power LED is on (red)
2. Verify antenna is connected
3. Ensure correct mode switch setting
4. Try power cycling the device
5. Try binary protocol version

## After Reading Configuration

**IMPORTANT:** Set device back to **Mode 0** for normal operation!

```
DIP Switch Position for Mode 0 (Normal):
┌─────┬─────┐
│  1  │  2  │
│ ON  │ ON  │
└─────┴─────┘
  M1    M0
```

## References

- **Manual:** E90-DTU(433C33)_UserManual_EN_v1.5.pdf
- **Manufacturer:** Chengdu Ebyte Electronic Technology Co., Ltd.
- **Support:** support@cdebyte.com
- **Website:** https://www.cdebyte.com

## Device Specifications

| Parameter | Value |
|-----------|-------|
| Frequency | 433MHz (425-450.5MHz) |
| TX Power | Up to 2W (33dBm) |
| Distance | Up to 4km (open area) |
| Interface | RS232/RS485 |
| Power | 10-28V DC |
| Baud Rate | 1200-115200 bps |
| Temperature | -40°C to +85°C |
| Dimensions | 82×62×25 mm |

## Notes

1. **Never** power on without antenna connected!
2. Communication distance depends on environment
3. Keep 50% distance margin for reliable communication
4. Use 12V or 24V DC power supply (recommended)
5. For multiple devices in same area, use 2MHz+ channel spacing
