#!/usr/bin/python3
"""
E90-DTU(433C33) Configuration Reader
Reads and displays current configuration from E90-DTU wireless modem

Usage:
    python3 e90_dtu_config_reader.py [--port PORT] [--baud BAUDRATE]

Note: Device must be in Mode 2 (Command mode) with M1=OFF, M0=ON
"""

import serial
import time
import argparse
import sys

class E90DTUConfigReader:
    def __init__(self, port='/dev/ttyUSB0', baudrate=9600, timeout=2):
        """
        Initialize E90-DTU configuration reader

        Args:
            port: Serial port device (default: /dev/ttyUSB0)
            baudrate: Serial baudrate (default: 9600)
            timeout: Serial timeout in seconds (default: 2)
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None

    def connect(self):
        """Open serial connection to E90-DTU"""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout
            )
            time.sleep(0.5)  # Allow time for connection to stabilize
            print(f"✓ Connected to {self.port} at {self.baudrate} baud")
            return True
        except serial.SerialException as e:
            print(f"✗ Error connecting to {self.port}: {e}")
            return False

    def disconnect(self):
        """Close serial connection"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print(f"✓ Disconnected from {self.port}")

    def send_command(self, command, wait_time=0.5):
        """
        Send AT command and read response

        Args:
            command: AT command string (without \r\n)
            wait_time: Time to wait for response in seconds

        Returns:
            Response string or None on error
        """
        if not self.ser or not self.ser.is_open:
            print("✗ Serial port not open")
            return None

        try:
            # Clear input buffer
            self.ser.reset_input_buffer()

            # Send command
            cmd = f"{command}\r\n".encode('ascii')
            self.ser.write(cmd)
            print(f"→ Sent: {command}")

            # Wait for response
            time.sleep(wait_time)

            # Read response
            response = b""
            while self.ser.in_waiting > 0:
                response += self.ser.read(self.ser.in_waiting)
                time.sleep(0.1)

            if response:
                decoded = response.decode('ascii', errors='ignore').strip()
                print(f"← Received: {decoded}")
                return decoded
            else:
                print("← No response")
                return None

        except Exception as e:
            print(f"✗ Error sending command '{command}': {e}")
            return None

    def parse_lora_config(self, response):
        """Parse AT+LORA response and return configuration dictionary"""
        config = {}

        if not response or "ERROR" in response:
            return config

        # Remove AT+LORA= prefix if present
        if "AT+LORA=" in response:
            response = response.split("AT+LORA=")[1]

        # Parse comma-separated values
        # Expected format: ADDR,NETID,AIRBAUD,PACKLEN,RSSI_EN,TXPOW,CH,RSSI_DATA,TR_MOD,RELAY,LBT,WOR,WOR_TIM,CRYPT
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
            print(f"✗ Error parsing configuration: {e}")

        return config

    def read_configuration(self):
        """Read all configuration parameters from E90-DTU"""
        print("\n" + "="*60)
        print("E90-DTU(433C33) Configuration Reader")
        print("="*60)

        config = {}

        # Test connection with AT
        print("\n[1/4] Testing communication...")
        response = self.send_command("AT")
        if response and ("OK" in response or "AT" in response):
            print("✓ Device responding")
        else:
            print("✗ Device not responding. Check connection and mode switch.")
            print("   Note: Device must be in Mode 2 (M1=OFF, M0=ON)")
            return None

        # Get device version
        print("\n[2/4] Reading device version...")
        response = self.send_command("AT+VER")
        if response:
            config['version'] = response

        # Get LoRa configuration
        print("\n[3/4] Reading LoRa configuration...")
        response = self.send_command("AT+LORA")
        if response:
            lora_config = self.parse_lora_config(response)
            config.update(lora_config)

        # Get UART configuration
        print("\n[4/4] Reading UART configuration...")
        response = self.send_command("AT+UART")
        if response:
            config['uart'] = response

        return config

    def display_configuration(self, config):
        """Display configuration in human-readable format"""
        if not config:
            print("\n✗ No configuration data available")
            return

        print("\n" + "="*60)
        print("CONFIGURATION SUMMARY")
        print("="*60)

        # Device Information
        if 'version' in config:
            print(f"\n📋 Device Version:")
            print(f"   {config['version']}")

        # UART Settings
        if 'uart' in config:
            print(f"\n🔌 UART Configuration:")
            print(f"   {config['uart']}")

        # LoRa Settings
        if 'address' in config:
            print(f"\n📡 LoRa Configuration:")
            print(f"   Station Address:     {config.get('address', 'N/A')}")
            print(f"   Network ID:          {config.get('network_id', 'N/A')}")
            print(f"   Channel:             {config.get('channel', 'N/A')}")

            # Calculate frequency (433MHz base)
            try:
                ch = int(config.get('channel', 0))
                freq = 425.0 + (ch * 0.1)  # 100kHz channel spacing
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

        print("\n" + "="*60)

    def _decode_power(self, power_code):
        """Decode power level code"""
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


def main():
    parser = argparse.ArgumentParser(
        description='E90-DTU(433C33) Configuration Reader',
        epilog='Note: Device must be in Mode 2 (Command mode) with M1=OFF, M0=ON'
    )
    parser.add_argument(
        '--port', '-p',
        default='/dev/ttyUSB0',
        help='Serial port (default: /dev/ttyUSB0)'
    )
    parser.add_argument(
        '--baud', '-b',
        type=int,
        default=9600,
        help='Baudrate (default: 9600)'
    )
    parser.add_argument(
        '--timeout', '-t',
        type=float,
        default=2.0,
        help='Serial timeout in seconds (default: 2.0)'
    )

    args = parser.parse_args()

    # Create reader instance
    reader = E90DTUConfigReader(
        port=args.port,
        baudrate=args.baud,
        timeout=args.timeout
    )

    # Connect to device
    if not reader.connect():
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
        print("\n💡 Remember to set device back to Mode 0 (M1=ON, M0=ON) for normal operation")


if __name__ == "__main__":
    main()
