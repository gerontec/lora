# E90-DTU Network Configuration Reader

Read configuration from E90-DTU Ethernet models over TCP/IP network.

## Supported Models

- E90-DTU(xxxSLxx-ETH) - Ethernet versions with RJ45 connector
- E90-DTU with WiFi/Ethernet expansion modules
- Any E90-DTU with network connectivity

## Default Network Settings

Based on factory defaults for most Ebyte E90-DTU Ethernet models:

| Parameter | Default Value |
|-----------|---------------|
| IP Address | 192.168.4.101 |
| Subnet Mask | 255.255.255.0 |
| Gateway | 192.168.4.1 |
| Config Port | 8886 |
| Data Port | 8080 (varies by model) |

## Quick Start

### Basic Usage

```bash
# Use factory defaults (192.168.4.101:8886)
python3 e90_dtu_config_reader_network.py

# Specify custom IP and port
python3 e90_dtu_config_reader_network.py --ip 192.168.1.100 --port 8886

# Scan common ports to find configuration port
python3 e90_dtu_config_reader_network.py --ip 192.168.4.101 --scan-ports
```

### Command Line Options

```bash
python3 e90_dtu_config_reader_network.py [OPTIONS]

Options:
  --ip, -i IP          Device IP address (default: 192.168.4.101)
  --port, -p PORT      TCP port (default: 8886)
  --timeout, -t SEC    Socket timeout in seconds (default: 5.0)
  --scan-ports         Scan common ports to find config port
  --help               Show help message
```

## Network Setup

### Step 1: Connect Device to Network

**Option A: Direct Connection**
```
Computer <---> Ethernet Cable <---> E90-DTU
```

Set your computer's network adapter:
- IP: 192.168.4.100
- Subnet: 255.255.255.0
- Gateway: 192.168.4.1

**Option B: Via Router/Switch**
```
Computer <---> Router/Switch <---> E90-DTU
```

Ensure both devices are on the same subnet.

### Step 2: Test Connectivity

```bash
# Ping the device
ping 192.168.4.101

# Expected output:
# 64 bytes from 192.168.4.101: icmp_seq=1 ttl=64 time=1.2 ms
```

### Step 3: Find Configuration Port

If unsure about the port, use the port scanner:

```bash
python3 e90_dtu_config_reader_network.py --scan-ports
```

This will test common ports:
- 8886 (common configuration port)
- 8080 (common data port)
- 8899 (alternative config port)
- 23 (Telnet)
- 80 (HTTP/Web interface)
- 9000 (alternative)
- 10000 (alternative)

## Expected Output

```
==============================================================
E90-DTU Network Configuration Reader
Device: 192.168.4.101:8886
==============================================================

[1/5] Testing communication with AT command...
→ Sent: AT
← Received: OK
✓ Device responding to AT commands

[2/5] Reading device information...
→ Sent: AT+VER
← Received: AT+VER=E90-DTU(433SL22-ETH) V2.0

[3/5] Reading network settings...
→ Sent: AT+NET
← Received: AT+NET=192.168.4.101,255.255.255.0,192.168.4.1

[4/5] Reading radio configuration...
→ Sent: AT+LORA
← Received: AT+LORA=0,0,9600,240,RSCHOFF,PWMAX,80,RSDATOFF...

[5/5] Reading UART configuration...
→ Sent: AT+UART
← Received: AT+UART=9600,8N1

==============================================================
CONFIGURATION SUMMARY
==============================================================

🌐 Network Connection:
   IP Address:          192.168.4.101
   TCP Port:            8886
   Protocol:            AT commands

📋 Device Information:
   AT+VER=E90-DTU(433SL22-ETH) V2.0

🔌 Network Settings:
   AT+NET=192.168.4.101,255.255.255.0,192.168.4.1

🔧 UART Configuration:
   AT+UART=9600,8N1

📡 Radio Configuration:
   Station Address:     0
   Network ID:          0
   Channel:             80
   Frequency:           433.0 MHz
   Air Baudrate:        9600 bps
   Packet Length:       240 bytes
   TX Power:            2W (33dBm)
   Transfer Mode:       Transparent transmission
   ...

==============================================================
```

## Troubleshooting

### Cannot Connect to Device

**1. Check Network Connectivity**
```bash
# Ping the device
ping 192.168.4.101

# Check if port is open (requires nmap)
nmap -p 8886 192.168.4.101

# Or use netcat
nc -zv 192.168.4.101 8886
```

**2. Check IP Address**

The device might not be using the default IP. Options:

A. **Use network scanner** (requires nmap):
```bash
nmap -sn 192.168.4.0/24
```

B. **Check via web interface**:
- Try http://192.168.4.101 in a browser
- Many E90-DTU models have a web configuration interface

C. **Reset to factory defaults**:
- Check device manual for reset procedure
- Usually involves a physical button or DIP switch combination

**3. Check Firewall**

Temporarily disable firewall or add exception:
```bash
# Linux
sudo ufw allow 8886/tcp

# Check if connection is blocked
sudo iptables -L -n | grep 8886
```

**4. Try Different Ports**

Common configuration ports for Ebyte DTU devices:
```bash
# Test multiple ports
for port in 8886 8080 8899 23 80; do
    echo "Testing port $port..."
    python3 e90_dtu_config_reader_network.py --ip 192.168.4.101 --port $port
done
```

### No AT Response

**1. Check Configuration Mode**

Some devices require entering configuration mode:
- Via web interface
- Via DIP switch setting
- Via serial command before network access

**2. Try Binary Protocol**

Some firmware versions may use binary protocol:
- The script automatically tries binary commands if AT fails
- Look for "Trying binary protocol..." in output

**3. Check Web Interface**

Many E90-DTU Ethernet models have a web interface:
```bash
# Open in browser
http://192.168.4.101

# Common credentials:
# Username: admin
# Password: admin (or 123456)
```

### Wrong Subnet

If device is on different subnet:

**Option A: Change your computer's IP**
```bash
# Linux
sudo ip addr add 192.168.4.100/24 dev eth0

# Or use Network Manager GUI
```

**Option B: Configure routing**
```bash
# Add route to device subnet
sudo route add -net 192.168.4.0 netmask 255.255.255.0 gw YOUR_GATEWAY
```

## Common Port Numbers

| Port | Purpose | Notes |
|------|---------|-------|
| 8886 | Configuration | Most common config port |
| 8080 | Data transmission | Default data port |
| 8899 | Alternative config | Some firmware versions |
| 23 | Telnet | Older models |
| 80 | HTTP | Web interface |
| 9000 | Custom | User configurable |
| 10000 | Custom | User configurable |

## AT Commands Reference

Common AT commands for E90-DTU:

```bash
AT              # Test connection
AT+VER          # Get version
AT+LORA         # Get/Set LoRa parameters
AT+UART         # Get/Set UART settings
AT+NET          # Get/Set network settings
AT+NETIP        # Get/Set IP address
AT+NETPORT      # Get/Set port numbers
AT+NETMODE      # Get/Set network mode
AT+RESET        # Restart device
AT+DEFAULT      # Reset to factory defaults
```

## Network Security Notes

⚠️ **Important Security Considerations:**

1. **Change Default Credentials**
   - Default passwords are well-known
   - Change via web interface or AT commands

2. **Isolate Network**
   - Don't expose DTU directly to internet
   - Use firewall rules to restrict access
   - Consider VPN for remote access

3. **Firmware Updates**
   - Check manufacturer website for updates
   - Updates may fix security vulnerabilities

4. **Monitor Access**
   - Log all configuration changes
   - Monitor for unusual network activity

## Python Network Testing

Simple test script to check connectivity:

```python
#!/usr/bin/python3
import socket

ip = "192.168.4.101"
port = 8886

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    sock.connect((ip, port))
    print(f"✓ Connected to {ip}:{port}")

    # Send AT command
    sock.sendall(b"AT\r\n")
    response = sock.recv(1024)
    print(f"Response: {response}")

    sock.close()
except Exception as e:
    print(f"✗ Error: {e}")
```

## Integration Examples

### Python Script Integration

```python
from e90_dtu_config_reader_network import E90DTUNetworkReader

# Create reader
reader = E90DTUNetworkReader(ip='192.168.4.101', port=8886)

# Connect and read
if reader.connect():
    config = reader.read_configuration()
    reader.display_configuration(config)
    reader.disconnect()
```

### Automated Monitoring

```bash
#!/bin/bash
# Monitor E90-DTU configuration periodically

while true; do
    echo "=== $(date) ==="
    python3 e90_dtu_config_reader_network.py --ip 192.168.4.101 | tee -a dtu_monitor.log
    sleep 3600  # Check every hour
done
```

## Additional Resources

- **Manual**: E90-DTU(xxxSLxx-ETH)-V2.0_UserManual_EN_v1.0.pdf
- **Manufacturer**: Chengdu Ebyte Electronic Technology Co., Ltd.
- **Website**: https://www.cdebyte.com
- **Support**: support@cdebyte.com

## Comparison: Serial vs Network

| Feature | Serial (RS232/485) | Network (Ethernet/WiFi) |
|---------|-------------------|------------------------|
| Connection | Direct cable | TCP/IP network |
| Distance | Limited (~15m RS232) | Unlimited (via network) |
| Multiple Access | One at a time | Multiple connections |
| Speed | Up to 115200 bps | 10/100 Mbps |
| Configuration | DIP switch mode | Web/AT commands |
| Setup Complexity | Simple | Moderate |
| Remote Access | No | Yes (with network) |

## Related Scripts

- `e90_dtu_config_reader.py` - Serial AT command version
- `e90_dtu_config_reader_binary.py` - Serial binary protocol version
- `e90_dtu_config_reader_network.py` - **This script** - Network version
