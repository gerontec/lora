# E90-DTU Configuration Tools

Complete toolkit for reading and managing E90-DTU wireless modem configurations.

## Available Scripts

### 1. Serial/RS232/RS485 Readers

#### AT Command Reader (Recommended)
```bash
python3 e90_dtu_config_reader.py --port /dev/ttyUSB0
```
- Uses AT commands over serial
- Most compatible with modern firmware
- Human-readable output
- **Documentation:** `README_E90_DTU_CONFIG.md`

#### Binary Protocol Reader
```bash
python3 e90_dtu_config_reader_binary.py --port /dev/ttyUSB0
```
- Uses binary protocol (0xC1 commands)
- Alternative for devices that don't support AT commands
- Lower-level access to registers
- **Documentation:** `README_E90_DTU_CONFIG.md`

### 2. Network/Ethernet Readers

#### Network Configuration Reader
```bash
python3 e90_dtu_config_reader_network.py --ip 192.168.4.101 --port 8886
```
- For E90-DTU models with Ethernet/WiFi
- Reads configuration over TCP/IP
- Supports port scanning
- **Documentation:** `README_E90_DTU_NETWORK.md`

#### Network Diagnostic Tool
```bash
python3 e90_dtu_network_test.py --ip 192.168.4.101
```
- Tests network connectivity
- Finds open ports
- Identifies configuration ports
- Can scan entire subnets
- **Documentation:** `README_E90_DTU_NETWORK.md`

## Quick Reference

### When to Use Each Script

| Situation | Script to Use |
|-----------|---------------|
| Serial connection (USB/RS232/RS485) | `e90_dtu_config_reader.py` |
| Serial not working with AT commands | `e90_dtu_config_reader_binary.py` |
| Ethernet/WiFi model | `e90_dtu_config_reader_network.py` |
| Don't know IP/port | `e90_dtu_network_test.py` |
| Network troubleshooting | `e90_dtu_network_test.py` |

### Common Command Examples

```bash
# ===== SERIAL =====

# Basic serial read (factory default: 9600 baud)
python3 e90_dtu_config_reader.py

# Custom port and baudrate
python3 e90_dtu_config_reader.py --port /dev/ttyUSB1 --baud 115200

# Binary protocol
python3 e90_dtu_config_reader_binary.py --port /dev/ttyUSB0

# ===== NETWORK =====

# Read from default IP (192.168.4.101:8886)
python3 e90_dtu_config_reader_network.py

# Custom IP and port
python3 e90_dtu_config_reader_network.py --ip 192.168.1.100 --port 8080

# Scan for configuration port
python3 e90_dtu_config_reader_network.py --ip 192.168.4.101 --scan-ports

# ===== DIAGNOSTICS =====

# Test connectivity to specific device
python3 e90_dtu_network_test.py --ip 192.168.4.101

# Scan entire subnet for E90-DTU devices
python3 e90_dtu_network_test.py --scan-subnet 192.168.4.0/24

# Test custom ports
python3 e90_dtu_network_test.py --ip 192.168.4.101 --ports 8886,9000,10000
```

## Device Setup

### Serial Connection Setup

1. **Set to Configuration Mode:**
   - DIP Switch: M1=OFF, M0=ON (Mode 2)
   - Power cycle device

2. **Connect:**
   - RS232: DB-9 connector
   - RS485: A/B terminals

3. **Read config:**
   ```bash
   python3 e90_dtu_config_reader.py
   ```

4. **Return to Normal:**
   - DIP Switch: M1=ON, M0=ON (Mode 0)

### Network Connection Setup

1. **Connect to network:**
   - Direct: Computer ↔ E90-DTU
   - Via switch/router

2. **Find device:**
   ```bash
   python3 e90_dtu_network_test.py --scan-subnet 192.168.4.0/24
   ```

3. **Read config:**
   ```bash
   python3 e90_dtu_config_reader_network.py --ip 192.168.4.101
   ```

## Configuration Parameters

All scripts display these parameters:

| Parameter | Description | Range |
|-----------|-------------|-------|
| Station Address | Device address for filtering | 0-65535 |
| Network ID | Network group ID | 0-255 |
| Channel | Frequency channel | 0-255 |
| Frequency | Actual RF frequency | 425-450.5 MHz |
| TX Power | Transmission power | 21-33 dBm |
| Air Baudrate | Wireless data rate | 1200-115200 |
| UART Baudrate | Serial port speed | 1200-115200 |
| Transfer Mode | Transparent/Fixed | TRNOR/TRFIX |

## Troubleshooting

### Serial Connection Issues

**No response from device:**
```bash
# Check port exists
ls -l /dev/ttyUSB*

# Fix permissions
sudo chmod 666 /dev/ttyUSB0

# Verify mode switch (M1=OFF, M0=ON)
# Try binary protocol
python3 e90_dtu_config_reader_binary.py
```

**Permission denied:**
```bash
sudo usermod -a -G dialout $USER
# Then logout/login
```

### Network Connection Issues

**Cannot find device:**
```bash
# Ping test
ping 192.168.4.101

# Subnet scan
python3 e90_dtu_network_test.py --scan-subnet 192.168.4.0/24

# Check web interface
xdg-open http://192.168.4.101
```

**Port not responding:**
```bash
# Test all common ports
python3 e90_dtu_config_reader_network.py --scan-ports

# Or use diagnostic tool
python3 e90_dtu_network_test.py --ip 192.168.4.101
```

## Installation Requirements

```bash
# Python 3 (usually pre-installed)
python3 --version

# Serial library (for serial readers)
pip3 install pyserial

# No additional libraries needed for network readers
```

## Supported Models

### Serial Models
- E90-DTU(433C33) - 433MHz, RS232/RS485
- E90-DTU(433C30) - 433MHz, RS232/RS485
- E90-DTU(433C37) - 433MHz, high power
- E90-DTU(230N27) - 230MHz
- E90-DTU(230N33) - 230MHz
- E90-DTU(170L30) - 170MHz

### Network Models
- E90-DTU(xxxSL22-ETH) - With Ethernet
- E90-DTU with WiFi module
- Any E90-DTU with network expansion

## File Structure

```
lora/
├── e90_dtu_config_reader.py              # Serial AT command reader
├── e90_dtu_config_reader_binary.py       # Serial binary reader
├── e90_dtu_config_reader_network.py      # Network reader
├── e90_dtu_network_test.py               # Network diagnostic tool
├── README_E90_DTU.md                     # This file - overview
├── README_E90_DTU_CONFIG.md              # Serial connection guide
└── README_E90_DTU_NETWORK.md             # Network connection guide
```

## Default Settings Reference

### Serial (Factory Defaults)
- Baudrate: 9600 bps
- Parity: 8N1
- Station Address: 0
- Channel: 80 (433.0 MHz)
- TX Power: Maximum

### Network (Factory Defaults)
- IP Address: 192.168.4.101
- Subnet Mask: 255.255.255.0
- Gateway: 192.168.4.1
- Config Port: 8886
- Data Port: 8080

## Related Files

- `E90-DTU(433C33)_UserManual_EN_v1.5.pdf` - Serial model manual
- `E90-DTU(xxxSLxx-ETH)-V2.0_UserManual_EN_v1.0.pdf` - Network model manual

## Support

- **Manufacturer:** Chengdu Ebyte Electronic Technology Co., Ltd.
- **Website:** https://www.cdebyte.com
- **Email:** support@cdebyte.com

## Safety Warnings

⚠️ **Important:**
- Always connect antenna before powering on
- Use 50Ω antenna only
- Recommended power: 12V or 24V DC
- Operating temperature: -40°C to +85°C
- Do not transmit continuously at max power
