#!/usr/bin/python3
"""
E90-DTU Ethernet Configuration Reader
Reads configuration from E90-DTU devices over TCP/IP network

Usage:
    python3 e90_dtu_config_reader_network.py --ip 192.168.4.101 --port 8886

Default settings:
    IP:   192.168.4.101 (factory default)
    Port: 8886 (configuration port)

Note: Device must be in configuration mode (AT command mode)
      Some models may require web interface or specific mode setting
"""

import socket
import time
import argparse
import sys

class E90DTUNetworkReader:
    def __init__(self, ip='192.168.4.101', port=8886, timeout=5):
        """
        Initialize E90-DTU network configuration reader

        Args:
            ip: Device IP address (default: 192.168.4.101)
            port: TCP port (default: 8886 for configuration)
            timeout: Socket timeout in seconds (default: 5)
        """
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.sock = None

    def connect(self):
        """Connect to E90-DTU via TCP socket"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(self.timeout)

            print(f"🔌 Connecting to {self.ip}:{self.port}...")
            self.sock.connect((self.ip, self.port))

            time.sleep(0.5)  # Allow connection to stabilize
            print(f"✓ Connected to {self.ip}:{self.port}")
            return True

        except socket.timeout:
            print(f"✗ Connection timeout to {self.ip}:{self.port}")
            print(f"   Check that device is powered on and network is reachable")
            return False
        except ConnectionRefusedError:
            print(f"✗ Connection refused by {self.ip}:{self.port}")
            print(f"   Check that port {self.port} is correct (try 8080, 8899, or 23)")
            return False
        except OSError as e:
            print(f"✗ Network error: {e}")
            print(f"   Check IP address and network connectivity")
            return False
        except Exception as e:
            print(f"✗ Error connecting: {e}")
            return False

    def disconnect(self):
        """Close TCP socket connection"""
        if self.sock:
            try:
                self.sock.close()
                print(f"✓ Disconnected from {self.ip}:{self.port}")
            except:
                pass

    def send_command(self, command, wait_time=1.0, encoding='ascii'):
        """
        Send AT command and read response

        Args:
            command: AT command string (without \r\n)
            wait_time: Time to wait for response in seconds
            encoding: Character encoding (ascii, utf-8, or latin-1)

        Returns:
            Response string or None on error
        """
        if not self.sock:
            print("✗ Socket not connected")
            return None

        try:
            # Send command
            cmd = f"{command}\r\n".encode(encoding)
            self.sock.sendall(cmd)
            print(f"→ Sent: {command}")

            # Wait for response
            time.sleep(wait_time)

            # Read response (with timeout handling)
            response = b""
            self.sock.settimeout(0.5)  # Short timeout for receiving

            try:
                while True:
                    chunk = self.sock.recv(4096)
                    if not chunk:
                        break
                    response += chunk
                    time.sleep(0.05)  # Small delay between chunks
            except socket.timeout:
                pass  # No more data available

            # Restore original timeout
            self.sock.settimeout(self.timeout)

            if response:
                try:
                    decoded = response.decode(encoding, errors='ignore').strip()
                    print(f"← Received: {decoded}")
                    return decoded
                except:
                    # Try hex display if decoding fails
                    print(f"← Received (hex): {response.hex().upper()}")
                    return response.hex()
            else:
                print("← No response")
                return None

        except socket.timeout:
            print("← Timeout waiting for response")
            return None
        except Exception as e:
            print(f"✗ Error sending command '{command}': {e}")
            return None

    def send_binary_command(self, command, wait_time=1.0):
        """
        Send binary command and read response

        Args:
            command: Binary command as bytearray or bytes
            wait_time: Time to wait for response

        Returns:
            Response bytes or None
        """
        if not self.sock:
            print("✗ Socket not connected")
            return None

        try:
            self.sock.sendall(command)
            print(f"→ Sent (hex): {command.hex().upper()}")

            time.sleep(wait_time)

            response = b""
            self.sock.settimeout(0.5)

            try:
                while True:
                    chunk = self.sock.recv(4096)
                    if not chunk:
                        break
                    response += chunk
                    time.sleep(0.05)
            except socket.timeout:
                pass

            self.sock.settimeout(self.timeout)

            if response:
                print(f"← Received (hex): {response.hex().upper()}")
                return response
            else:
                print("← No response")
                return None

        except Exception as e:
            print(f"✗ Error sending binary command: {e}")
            return None

    def read_configuration(self):
        """Read all configuration parameters from E90-DTU over network"""
        print("\n" + "="*60)
        print("E90-DTU Network Configuration Reader")
        print(f"Device: {self.ip}:{self.port}")
        print("="*60)

        config = {}

        # Test connection with AT
        print("\n[1/5] Testing communication with AT command...")
        response = self.send_command("AT", wait_time=1.0)
        if response and ("OK" in response or "AT" in response):
            print("✓ Device responding to AT commands")
        else:
            print("⚠ No AT response. Trying alternative methods...")

            # Try without CR/LF
            print("\n   Trying raw AT command...")
            response = self.send_command("AT", wait_time=0.5)

            # Try binary command
            if not response:
                print("\n   Trying binary protocol...")
                binary_cmd = bytearray([0xC1, 0x00, 0x09])
                response = self.send_binary_command(binary_cmd, wait_time=1.0)
                if response:
                    print("✓ Device responding to binary commands")
                    config['protocol'] = 'binary'
                else:
                    print("⚠ Device may not be in configuration mode")
                    print("   Try accessing via web interface or check port number")

        # Get device version/model
        print("\n[2/5] Reading device information...")
        response = self.send_command("AT+VER", wait_time=1.0)
        if response:
            config['version'] = response
        else:
            # Try alternative version commands
            for cmd in ["AT+GMR", "ATI", "AT+MODEL"]:
                response = self.send_command(cmd, wait_time=0.5)
                if response:
                    config['version'] = response
                    break

        # Get network configuration
        print("\n[3/5] Reading network settings...")
        response = self.send_command("AT+NET", wait_time=1.0)
        if response:
            config['network'] = response
        else:
            # Try alternatives
            for cmd in ["AT+NETIP", "AT+IPCONF", "AT+TCPIP"]:
                response = self.send_command(cmd, wait_time=0.5)
                if response:
                    config['network'] = response
                    break

        # Get LoRa/Radio configuration
        print("\n[4/5] Reading radio configuration...")
        response = self.send_command("AT+LORA", wait_time=1.0)
        if response:
            lora_config = self.parse_lora_config(response)
            config.update(lora_config)
        else:
            # Try alternative radio commands
            for cmd in ["AT+RF", "AT+RADIO", "AT+PARAM"]:
                response = self.send_command(cmd, wait_time=0.5)
                if response:
                    config['radio'] = response
                    break

        # Get UART configuration
        print("\n[5/5] Reading UART configuration...")
        response = self.send_command("AT+UART", wait_time=1.0)
        if response:
            config['uart'] = response

        return config

    def parse_lora_config(self, response):
        """Parse AT+LORA response"""
        config = {}

        if not response or "ERROR" in response:
            return config

        if "AT+LORA=" in response:
            response = response.split("AT+LORA=")[1]

        try:
            parts = response.split(',')
            if len(parts) >= 14:
                config['address'] = parts[0]
                config['network_id'] = parts[1]
                config['air_baudrate'] = parts[2]
                config['packet_length'] = parts[3]
                config['rssi_ambient'] = parts[4]
                config['tx_power'] = parts[5]
                config['channel'] = parts[6]
                config['rssi_data'] = parts[7]
                config['transfer_mode'] = parts[8]
                config['relay'] = parts[9]
                config['lbt'] = parts[10]
                config['wor_mode'] = parts[11]
                config['wor_timing'] = parts[12]
                config['encryption'] = parts[13]
        except Exception as e:
            print(f"⚠ Error parsing LoRa config: {e}")

        return config

    def display_configuration(self, config):
        """Display configuration in human-readable format"""
        if not config:
            print("\n✗ No configuration data available")
            return

        print("\n" + "="*60)
        print("CONFIGURATION SUMMARY")
        print("="*60)

        # Connection info
        print(f"\n🌐 Network Connection:")
        print(f"   IP Address:          {self.ip}")
        print(f"   TCP Port:            {self.port}")
        print(f"   Protocol:            {config.get('protocol', 'AT commands')}")

        # Device Information
        if 'version' in config:
            print(f"\n📋 Device Information:")
            print(f"   {config['version']}")

        # Network Settings
        if 'network' in config:
            print(f"\n🔌 Network Settings:")
            print(f"   {config['network']}")

        # UART Settings
        if 'uart' in config:
            print(f"\n🔧 UART Configuration:")
            print(f"   {config['uart']}")

        # Radio/LoRa Settings
        if 'address' in config:
            print(f"\n📡 Radio Configuration:")
            print(f"   Station Address:     {config.get('address', 'N/A')}")
            print(f"   Network ID:          {config.get('network_id', 'N/A')}")
            print(f"   Channel:             {config.get('channel', 'N/A')}")

            # Calculate frequency
            try:
                ch = int(config.get('channel', 0))
                freq = 425.0 + (ch * 0.1)
                print(f"   Frequency:           {freq:.1f} MHz")
            except:
                pass

            print(f"   Air Baudrate:        {config.get('air_baudrate', 'N/A')} bps")
            print(f"   Packet Length:       {config.get('packet_length', 'N/A')} bytes")
            print(f"   TX Power:            {self._decode_power(config.get('tx_power', ''))}")
            print(f"   Transfer Mode:       {self._decode_transfer_mode(config.get('transfer_mode', ''))}")
            print(f"   RSSI Ambient:        {config.get('rssi_ambient', 'N/A')}")
            print(f"   RSSI Data:           {config.get('rssi_data', 'N/A')}")
            print(f"   Relay:               {config.get('relay', 'N/A')}")
            print(f"   LBT:                 {config.get('lbt', 'N/A')}")
            print(f"   WOR Mode:            {config.get('wor_mode', 'N/A')}")
            print(f"   WOR Timing:          {config.get('wor_timing', 'N/A')} ms")
            print(f"   Encryption:          {config.get('encryption', 'N/A')}")

        elif 'radio' in config:
            print(f"\n📡 Radio Configuration:")
            print(f"   {config['radio']}")

        print("\n" + "="*60)

    def _decode_power(self, power_code):
        """Decode power level"""
        power_map = {
            'PWMAX': '2W (33dBm)',
            'PWMID': '1W (30dBm)',
            'PWLOW': '0.5W (27dBm)',
            'PWMIN': '0.1W (20dBm)'
        }
        return power_map.get(power_code, power_code)

    def _decode_transfer_mode(self, mode_code):
        """Decode transfer mode"""
        mode_map = {
            'TRNOR': 'Transparent transmission',
            'TRFIX': 'Fixed-point transmission'
        }
        return mode_map.get(mode_code, mode_code)

    def test_ports(self, ports):
        """Test multiple common ports to find the configuration port"""
        print(f"\n🔍 Testing common configuration ports on {self.ip}...")

        for port in ports:
            print(f"\n   Trying port {port}...")
            self.port = port

            if self.connect():
                response = self.send_command("AT", wait_time=0.5)
                self.disconnect()

                if response and ("OK" in response or "AT" in response):
                    print(f"   ✓ Port {port} responds to AT commands!")
                    return port
                else:
                    print(f"   ✗ Port {port} no AT response")

            time.sleep(0.5)

        print(f"\n   No responsive ports found. Try web interface or check device manual.")
        return None


def main():
    parser = argparse.ArgumentParser(
        description='E90-DTU Network Configuration Reader',
        epilog='Reads configuration from E90-DTU devices over TCP/IP'
    )
    parser.add_argument(
        '--ip', '-i',
        default='192.168.4.101',
        help='Device IP address (default: 192.168.4.101)'
    )
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=8886,
        help='TCP port (default: 8886)'
    )
    parser.add_argument(
        '--timeout', '-t',
        type=float,
        default=5.0,
        help='Socket timeout in seconds (default: 5.0)'
    )
    parser.add_argument(
        '--scan-ports',
        action='store_true',
        help='Scan common ports to find configuration port'
    )

    args = parser.parse_args()

    reader = E90DTUNetworkReader(
        ip=args.ip,
        port=args.port,
        timeout=args.timeout
    )

    # Port scanning mode
    if args.scan_ports:
        common_ports = [8886, 8080, 8899, 23, 80, 9000, 10000]
        found_port = reader.test_ports(common_ports)
        if found_port:
            args.port = found_port
            reader.port = found_port
        else:
            sys.exit(1)

    # Connect and read configuration
    if not reader.connect():
        print("\n💡 Troubleshooting:")
        print("   1. Check device is powered on")
        print("   2. Verify network connectivity: ping", args.ip)
        print("   3. Try --scan-ports to find the correct port")
        print("   4. Check device manual for correct configuration port")
        print("   5. Some models may require web interface configuration")
        sys.exit(1)

    try:
        # Read configuration
        config = reader.read_configuration()

        # Display results
        reader.display_configuration(config)

    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Disconnect
        reader.disconnect()
        print()


if __name__ == "__main__":
    main()
