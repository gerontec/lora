#!/usr/bin/python3
"""
E90-DTU(433C33) Configuration Reader (Binary Protocol)
Reads configuration using binary commands similar to E22 protocol

Usage:
    python3 e90_dtu_config_reader_binary.py [--port PORT]

Note: Device must be in Mode 2 (Command mode) with M1=OFF, M0=ON
"""

import serial
import time
import argparse
import sys

class E90DTUBinaryReader:
    def __init__(self, port='/dev/ttyUSB0', baudrate=9600, timeout=2):
        """Initialize E90-DTU binary protocol reader"""
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None

    def connect(self):
        """Open serial connection"""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout
            )
            time.sleep(0.5)
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

    def send_binary_command(self, command, wait_time=0.5):
        """Send binary command and read response"""
        if not self.ser or not self.ser.is_open:
            print("✗ Serial port not open")
            return None

        try:
            self.ser.reset_input_buffer()
            self.ser.write(command)
            print(f"→ Sent: {command.hex().upper()}")

            time.sleep(wait_time)

            response = b""
            while self.ser.in_waiting > 0:
                response += self.ser.read(self.ser.in_waiting)
                time.sleep(0.1)

            if response:
                print(f"← Received: {response.hex().upper()}")
                return response
            else:
                print("← No response")
                return None

        except Exception as e:
            print(f"✗ Error sending command: {e}")
            return None

    def read_all_parameters(self):
        """
        Read all parameters using C1 command
        Format: 0xC1 + Starting Address + Length
        """
        print("\n" + "="*60)
        print("E90-DTU(433C33) Binary Configuration Reader")
        print("="*60)

        # Try reading parameters (similar to E22 protocol)
        print("\n[1/3] Reading device parameters (Method 1: C1 command)...")
        command = bytearray([0xC1, 0x00, 0x09])  # Read 9 bytes from address 0x00
        response = self.send_binary_command(command, wait_time=1.0)

        if response and len(response) >= 3:
            self.parse_c1_response(response)
            return response

        # Try alternative command
        print("\n[2/3] Reading device parameters (Method 2: C3 command)...")
        command = bytearray([0xC3, 0x00, 0x09])  # Alternative read command
        response = self.send_binary_command(command, wait_time=1.0)

        if response and len(response) >= 3:
            self.parse_c3_response(response)
            return response

        # Try version command
        print("\n[3/3] Reading device version...")
        command = bytearray([0xC3, 0xC3, 0xC3])  # Version query
        response = self.send_binary_command(command, wait_time=1.0)

        if response:
            print(f"   Device version info: {response.hex().upper()}")

        return None

    def parse_c1_response(self, response):
        """Parse C1 command response"""
        if len(response) < 12:
            print(f"   Response too short: {len(response)} bytes (expected >= 12)")
            return

        print(f"\n📋 Configuration Data ({len(response)} bytes):")
        print(f"   Raw: {response.hex().upper()}")

        header = response[:3]
        data = response[3:]

        print(f"\n   Header: {header.hex().upper()}")
        print(f"   Data:   {data.hex().upper()}")

        if len(data) >= 9:
            print(f"\n📡 Parameter Interpretation:")
            print(f"   ADDH (0x00):        0x{data[0]:02X} ({data[0]:3d}) - Address High Byte")
            print(f"   ADDL (0x01):        0x{data[1]:02X} ({data[1]:3d}) - Address Low Byte")

            address = (data[0] << 8) | data[1]
            print(f"   → Station Address:  {address}")

            print(f"\n   NETID (0x02):       0x{data[2]:02X} ({data[2]:3d}) - Network ID")

            # REG0: UART and Air Speed
            reg0 = data[3]
            print(f"\n   REG0 (0x03):        0x{reg0:02X} ({reg0:08b}b)")
            uart_baud = ["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"][(reg0 >> 5) & 0x07]
            uart_parity = ["8N1", "8O1", "8E1", "8N1"][(reg0 >> 3) & 0x03]
            air_speed = ["2.4k", "2.4k", "2.4k", "2.4k", "4.8k", "9.6k", "15.6k", "21.9k"][reg0 & 0x07]
            print(f"   → UART Baud:        {uart_baud} bps")
            print(f"   → UART Parity:      {uart_parity}")
            print(f"   → Air Speed:        {air_speed} bps")

            # REG1: Sub-packet and Power
            reg1 = data[4]
            print(f"\n   REG1 (0x04):        0x{reg1:02X} ({reg1:08b}b)")
            sub_packet = ["240", "128", "64", "32"][(reg1 >> 6) & 0x03]
            rssi_ambient = "Enabled" if reg1 & 0x20 else "Disabled"
            tx_power = ["30dBm", "27dBm", "24dBm", "21dBm"][reg1 & 0x03]
            print(f"   → Sub-packet:       {sub_packet} bytes")
            print(f"   → RSSI Ambient:     {rssi_ambient}")
            print(f"   → TX Power:         {tx_power}")

            # REG2: Channel
            reg2 = data[5]
            print(f"\n   REG2 (0x05):        0x{reg2:02X} ({reg2:3d}) - Channel")
            freq_433 = 425.0 + (reg2 * 0.1)  # E90-DTU(433C33): 425-450.5MHz
            print(f"   → Frequency:        {freq_433:.1f} MHz (433MHz band)")

            # REG3: Options
            reg3 = data[6]
            print(f"\n   REG3 (0x06):        0x{reg3:02X} ({reg3:08b}b)")
            rssi_byte = "Enabled" if reg3 & 0x80 else "Disabled"
            transmission = "Fixed-point" if reg3 & 0x40 else "Transparent"
            relay = "Enabled" if reg3 & 0x20 else "Disabled"
            lbt = "Enabled" if reg3 & 0x10 else "Disabled"
            wor_mode = ["Transmitter", "Receiver", "Reserved", "Disabled"][(reg3 >> 3) & 0x03]
            wor_cycle = ["500ms", "1000ms", "1500ms", "2000ms", "2500ms", "3000ms", "3500ms", "4000ms"][reg3 & 0x07]
            print(f"   → RSSI Byte:        {rssi_byte}")
            print(f"   → Transmission:     {transmission}")
            print(f"   → Relay:            {relay}")
            print(f"   → LBT:              {lbt}")
            print(f"   → WOR Mode:         {wor_mode}")
            print(f"   → WOR Cycle:        {wor_cycle}")

            # CRYPT: Encryption key (write-only, may show as 0x00)
            if len(data) >= 9:
                crypt_h = data[7]
                crypt_l = data[8]
                crypt_key = (crypt_h << 8) | crypt_l
                print(f"\n   CRYPT_H (0x07):     0x{crypt_h:02X}")
                print(f"   CRYPT_L (0x08):     0x{crypt_l:02X}")
                if crypt_key == 0:
                    print(f"   → Encryption:       Disabled or masked (write-only)")
                else:
                    print(f"   → Encryption Key:   {crypt_key} (0x{crypt_key:04X})")

    def parse_c3_response(self, response):
        """Parse C3 command response (module info)"""
        print(f"\n📋 Module Information:")
        print(f"   Raw response: {response.hex().upper()}")

        if len(response) >= 4:
            print(f"   Model:    {response[0]:02X}")
            print(f"   Version:  {response[1]:02X}")
            print(f"   Features: {response[2]:02X}")


def main():
    parser = argparse.ArgumentParser(
        description='E90-DTU(433C33) Binary Configuration Reader',
        epilog='Note: Device must be in Mode 2 (M1=OFF, M0=ON)'
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

    args = parser.parse_args()

    reader = E90DTUBinaryReader(port=args.port, baudrate=args.baud)

    if not reader.connect():
        sys.exit(1)

    try:
        reader.read_all_parameters()

    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        reader.disconnect()
        print("\n💡 Remember to set device back to Mode 0 (M1=ON, M0=ON) for normal operation")
        print("\n" + "="*60)


if __name__ == "__main__":
    main()
