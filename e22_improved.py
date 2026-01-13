#!/usr/bin/python3
"""
E22 LoRa Module Configuration Tool
Based on official Ebyte E22 documentation (1:1 register mapping)
Supports E22-400 (433MHz), E22-900 (868/915MHz) series
"""
import serial
import time
import argparse
import logging
import sys

# Set up logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')


class E22Module:
    """Class to handle E22 LoRa module communication and configuration

    Register mapping according to official Ebyte documentation:
    - 00H: ADDH (Address High Byte)
    - 01H: ADDL (Address Low Byte)
    - 02H: NETID (Network ID)
    - 03H: REG0 (UART baud rate, parity, air rate)
    - 04H: REG1 (Sub-packet, RSSI ambient noise, transmit power)
    - 05H: REG2 (Channel Control)
    - 06H: REG3 (RSSI byte, transfer method, relay, LBT, WOR)
    - 07H: CRYPT_H (Key high byte, write only)
    - 08H: CRYPT_L (Key low byte, write only)
    - 80H-86H: PIDs (Product information 7 bytes)
    """

    # Official register mappings from Ebyte documentation
    BAUD_RATES = {
        0: "1200", 1: "2400", 2: "4800", 3: "9600",
        4: "19200", 5: "38400", 6: "57600", 7: "115200"
    }

    PARITY_MODES = {
        0: "8N1", 1: "8O1", 2: "8E1", 3: "8N1"  # 3 is equivalent to 0
    }

    # Note: First 3 air rates (0,1,2) are all 2.4k according to official docs
    AIR_RATES = {
        0: "2.4k", 1: "2.4k", 2: "2.4k", 3: "4.8k",
        4: "9.6k", 5: "19.2k", 6: "38.4k", 7: "62.5k"
    }

    SUB_PACKET_SIZES = {
        0: "240", 1: "128", 2: "64", 3: "32"
    }

    # Power levels differ by module series
    # E22-900 series (868/915 MHz): 33/30/27/24 dBm
    # E22-400 series (433 MHz): varies by model
    POWER_LEVELS_900 = {
        0: "33dBm", 1: "30dBm", 2: "27dBm", 3: "24dBm"
    }

    POWER_LEVELS_400 = {
        0: "22dBm", 1: "17dBm", 2: "13dBm", 3: "10dBm"
    }

    def __init__(self, port, baudrate=9600, timeout=1, module_type="auto"):
        """Initialize the E22 module connection

        Args:
            port: Serial port path (e.g., /dev/ttyUSB0)
            baudrate: Baud rate for serial communication
            timeout: Serial timeout in seconds
            module_type: "400" for E22-400 series, "900" for E22-900 series, "auto" for autodetect
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
        self.module_type = module_type

    def __enter__(self):
        """Context manager entry"""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def open(self):
        """Open serial connection"""
        if self.ser is None or not self.ser.is_open:
            self.ser = serial.Serial(self.port, baudrate=self.baudrate, timeout=self.timeout)
            time.sleep(0.1)  # Allow time for connection to stabilize

    def close(self):
        """Close serial connection"""
        if self.ser and self.ser.is_open:
            self.ser.close()

    def send_command(self, command):
        """Send a command to the module and receive response

        Args:
            command: Bytes to send

        Returns:
            Response bytes
        """
        logging.debug(f"Sending command: {command.hex()}")
        self.ser.write(command)
        time.sleep(0.1)
        response = self.ser.read(100)
        logging.debug(f"Received response: {response.hex()}")
        return response

    def read_config(self):
        """Read current module configuration (9 bytes from address 00H)

        Command: C1 00 09
        Response: C1 00 09 + 9 bytes of configuration

        Returns:
            9 bytes of configuration data
        """
        command = bytes([0xC1, 0x00, 0x09])
        response = self.send_command(command)
        if len(response) < 12:
            raise ValueError(f"Unexpected response length: {len(response)} bytes (expected >= 12). Response: {response.hex()}")
        if response[0:3] != bytes([0xC1, 0x00, 0x09]):
            raise ValueError(f"Unexpected response header: {response[0:3].hex()} (expected C10009)")
        return response[3:12]  # Return 9 bytes of configuration data

    def write_config(self, config):
        """Write configuration to module (C0 command)

        Command: C0 00 09 + 9 bytes
        Response: C1 00 09 + 9 bytes

        Args:
            config: List of 9 configuration bytes

        Returns:
            9 bytes of confirmed configuration
        """
        if len(config) != 9:
            raise ValueError(f"Configuration must be exactly 9 bytes, got {len(config)}")

        command = bytes([0xC0, 0x00, 0x09] + config)
        response = self.send_command(command)
        if response[0:3] != bytes([0xC1, 0x00, 0x09]):
            raise ValueError(f"Failed to write configuration. Response: {response.hex()}")
        return response[3:12]

    def write_encryption_keys(self, key_high, key_low):
        """Write encryption keys to module (addresses 07H and 08H)

        Args:
            key_high: High byte of encryption key (CRYPT_H)
            key_low: Low byte of encryption key (CRYPT_L)
        """
        command = bytes([0xC0, 0x07, 0x02, key_high, key_low])
        response = self.send_command(command)
        if response[0:3] != bytes([0xC1, 0x07, 0x02]):
            raise ValueError(f"Failed to write encryption keys. Response: {response.hex()}")

    def read_product_info(self):
        """Read product information (PIDs) from module

        Command: C1 80 07
        Response: C1 80 07 + 7 bytes of product info

        Returns:
            7 bytes of product information
        """
        command = bytes([0xC1, 0x80, 0x07])
        response = self.send_command(command)
        if len(response) < 10:
            raise ValueError(f"Unexpected product info response length: {len(response)} bytes. Response: {response.hex()}")
        return response[3:10]  # Return 7 bytes of product information

    def get_version(self):
        """Get firmware version information from module

        The C3 C3 C3 command is not documented in official Ebyte docs.
        Some modules support it, returning 3-4 bytes, others don't.

        Returns:
            Dictionary with version information, or None if not supported
        """
        command = bytes([0xC3, 0xC3, 0xC3])
        response = self.send_command(command)

        # Check if module supports version command
        if len(response) < 3:
            return None

        # Check if response is all zeros (unsupported)
        if response[0:3] == bytes([0xC3, 0x00, 0x00]):
            return None

        version_info = {
            'model': response[0] if len(response) > 0 else 0,
            'version': response[1] if len(response) > 1 else 0,
            'features': response[2] if len(response) > 2 else 0,
            'raw': response.hex().upper()
        }

        if len(response) > 3:
            version_info['extra'] = response[3]

        return version_info

    def read_rssi(self):
        """Read RSSI values from module

        Command: C0 C1 C2 C3 00 02
        Returns current ambient noise RSSI and last received RSSI

        Formula: dBm = -(256 - RSSI)

        Returns:
            Dictionary with RSSI values in dBm
        """
        command = bytes([0xC0, 0xC1, 0xC2, 0xC3, 0x00, 0x02])
        response = self.send_command(command)

        # Check if the response matches the expected format
        if len(response) != 5 or response.hex()[:6] != 'c10002':
            raise ValueError(f"Unexpected RSSI response format: {response.hex()}")

        # Extract RSSI values
        current_noise_rssi = response[3]
        last_received_rssi = response[4]

        # Apply formula from documentation: dBm = -(256 - RSSI)
        current_noise_dbm = -(256 - current_noise_rssi)
        last_received_dbm = -(256 - last_received_rssi)

        return {
            "current_noise_rssi": current_noise_dbm,
            "last_received_rssi": last_received_dbm
        }

    def detect_module_type(self, config):
        """Detect module type based on configuration

        Args:
            config: 9-byte configuration

        Returns:
            "400" for E22-400 series, "900" for E22-900 series
        """
        if self.module_type != "auto":
            return self.module_type

        # Try to detect based on channel/frequency range
        # E22-400: typically uses channels for 410-441 MHz
        # E22-900: typically uses channels for 850-930 MHz
        # This is a heuristic, may need adjustment
        channel = config[5]  # REG2

        # If channel > 30, likely 900MHz module (wider range)
        # This is just a guess, user should specify with --model flag
        if channel > 30:
            return "900"
        else:
            return "400"

    def parse_config(self, config):
        """Parse configuration bytes into readable format

        According to official Ebyte E22 register mapping:
        Byte 0: ADDH (00H)
        Byte 1: ADDL (01H)
        Byte 2: NETID (02H)
        Byte 3: REG0 (03H) - bits 7-5: UART baud, 4-3: parity, 2-0: air rate
        Byte 4: REG1 (04H) - bits 7-6: sub-packet, 5: RSSI ambient, 4-2: reserved, 1-0: power
        Byte 5: REG2 (05H) - channel
        Byte 6: REG3 (06H) - bits 7: RSSI byte, 6: transfer mode, 5: relay, 4: LBT, 3: WOR role, 2-0: WOR period
        Byte 7: REG4 (07H) - reserved
        Byte 8: REG5 (08H) - reserved

        Args:
            config: 9 bytes of configuration data

        Returns:
            Dictionary with parsed configuration
        """
        if len(config) != 9:
            raise ValueError(f"Configuration must be 9 bytes, got {len(config)}")

        addh, addl, netid, reg0, reg1, reg2, reg3, reg4, reg5 = config

        # Detect module type
        detected_type = self.detect_module_type(config)
        power_map = self.POWER_LEVELS_900 if detected_type == "900" else self.POWER_LEVELS_400

        # Parse address
        address = (addh << 8) | addl

        # Parse REG0 (03H)
        baud_rate_code = (reg0 >> 5) & 0x07
        parity_code = (reg0 >> 3) & 0x03
        air_rate_code = reg0 & 0x07

        baud_rate = self.BAUD_RATES.get(baud_rate_code, f"Unknown({baud_rate_code})")
        parity = self.PARITY_MODES.get(parity_code, f"Unknown({parity_code})")
        air_rate = self.AIR_RATES.get(air_rate_code, f"Unknown({air_rate_code})")

        # Parse REG1 (04H)
        sub_packet_code = (reg1 >> 6) & 0x03
        rssi_ambient_enable = bool(reg1 & 0x20)
        power_code = reg1 & 0x03

        sub_packet_size = self.SUB_PACKET_SIZES.get(sub_packet_code, f"Unknown({sub_packet_code})")
        power = power_map.get(power_code, f"Unknown({power_code})")

        # Parse REG2 (05H) - Channel
        channel = reg2

        # Calculate frequency based on module type
        if detected_type == "900":
            # E22-900 series: Frequency = 850.125 + CH * 1 MHz
            frequency_mhz = 850.125 + channel
        else:
            # E22-400 series: Frequency = 410.125 + CH * 1 MHz (approximate)
            frequency_mhz = 410.125 + channel

        # Parse REG3 (06H)
        rssi_byte_enable = bool(reg3 & 0x80)
        fixed_transmission = bool(reg3 & 0x40)
        relay_enable = bool(reg3 & 0x20)
        lbt_enable = bool(reg3 & 0x10)
        wor_transmitter = bool(reg3 & 0x08)
        wor_period_code = reg3 & 0x07

        # WOR period: T = (1 + WOR) * 500ms
        wor_period_ms = (wor_period_code + 1) * 500

        return {
            "module_type": detected_type,
            "address": address,
            "address_hex": f"0x{address:04X}",
            "network_id": netid,
            "network_id_hex": f"0x{netid:02X}",
            "channel": channel,
            "frequency_mhz": frequency_mhz,
            "uart_baud_rate": baud_rate,
            "uart_parity": parity,
            "air_rate": air_rate,
            "sub_packet_size": sub_packet_size,
            "rssi_ambient_enable": rssi_ambient_enable,
            "transmit_power": power,
            "rssi_byte_enable": rssi_byte_enable,
            "transmission_mode": "fixed-point" if fixed_transmission else "transparent",
            "relay_enable": relay_enable,
            "lbt_enable": lbt_enable,
            "wor_mode": "transmitter" if wor_transmitter else "receiver",
            "wor_period_ms": wor_period_ms,
            "raw_hex": config.hex(' ').upper()
        }

    @staticmethod
    def create_config(address, network_id, channel, air_rate, baud_rate, parity,
                     power, sub_packet_size="240", rssi_ambient_enable=False,
                     rssi_byte_enable=False, fixed_transmission=False,
                     relay_enable=False, lbt_enable=False, wor_transmitter=False,
                     wor_period_ms=500):
        """Create configuration bytes from parameters

        All parameters according to official Ebyte E22 register specification

        Args:
            address: Module address (0-65535)
            network_id: Network ID (0-255)
            channel: Channel number (0-83)
            air_rate: Air data rate ("2.4k", "4.8k", "9.6k", "19.2k", "38.4k", "62.5k")
            baud_rate: UART baud rate ("1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200")
            parity: Parity mode ("8N1", "8O1", "8E1")
            power: Transmit power (e.g., "33dBm", "30dBm", "27dBm", "24dBm" for E22-900)
            sub_packet_size: Sub-packet size ("240", "128", "64", "32")
            rssi_ambient_enable: Enable RSSI ambient noise reading
            rssi_byte_enable: Enable RSSI byte output with received data
            fixed_transmission: True for fixed-point, False for transparent
            relay_enable: Enable relay/repeater function
            lbt_enable: Enable Listen Before Talk
            wor_transmitter: True for WOR transmitter, False for WOR receiver
            wor_period_ms: WOR period in ms (500, 1000, 1500, 2000, 2500, 3000, 3500, 4000)

        Returns:
            List of 9 configuration bytes
        """
        # Byte 0-1: Address
        addh = (address >> 8) & 0xFF
        addl = address & 0xFF

        # Byte 2: Network ID
        netid = network_id & 0xFF

        # REG0 (Byte 3): UART baud rate, parity, air rate
        baud_codes = {"1200": 0, "2400": 1, "4800": 2, "9600": 3, "19200": 4, "38400": 5, "57600": 6, "115200": 7}
        parity_codes = {"8N1": 0, "8O1": 1, "8E1": 2}
        air_codes = {"2.4k": 2, "4.8k": 3, "9.6k": 4, "19.2k": 5, "38.4k": 6, "62.5k": 7}

        baud_code = baud_codes.get(baud_rate, 3)  # Default 9600
        parity_code = parity_codes.get(parity, 0)  # Default 8N1
        air_code = air_codes.get(air_rate, 2)  # Default 2.4k

        reg0 = (baud_code << 5) | (parity_code << 3) | air_code

        # REG1 (Byte 4): Sub-packet, RSSI ambient, power
        packet_codes = {"240": 0, "128": 1, "64": 2, "32": 3}
        # Try to extract power code from power string (e.g., "33dBm" -> 0)
        power_codes_900 = {"33dBm": 0, "30dBm": 1, "27dBm": 2, "24dBm": 3}
        power_codes_400 = {"22dBm": 0, "17dBm": 1, "13dBm": 2, "10dBm": 3}

        packet_code = packet_codes.get(sub_packet_size, 0)  # Default 240
        power_code = power_codes_900.get(power, power_codes_400.get(power, 0))  # Try both

        reg1 = (packet_code << 6) | power_code
        if rssi_ambient_enable:
            reg1 |= 0x20

        # REG2 (Byte 5): Channel
        reg2 = channel & 0xFF

        # REG3 (Byte 6): RSSI byte, transfer mode, relay, LBT, WOR
        wor_codes = {500: 0, 1000: 1, 1500: 2, 2000: 3, 2500: 4, 3000: 5, 3500: 6, 4000: 7}
        wor_code = wor_codes.get(wor_period_ms, 0)  # Default 500ms

        reg3 = wor_code
        if rssi_byte_enable:
            reg3 |= 0x80
        if fixed_transmission:
            reg3 |= 0x40
        if relay_enable:
            reg3 |= 0x20
        if lbt_enable:
            reg3 |= 0x10
        if wor_transmitter:
            reg3 |= 0x08

        # REG4, REG5: Reserved (0)
        reg4 = 0
        reg5 = 0

        return [addh, addl, netid, reg0, reg1, reg2, reg3, reg4, reg5]


def print_config(parsed_config):
    """Print module configuration in readable format

    Args:
        parsed_config: Dictionary with parsed configuration
    """
    print("\n" + "="*60)
    print("E22 MODULE CONFIGURATION")
    print("="*60)
    print(f"Module Type:     E22-{parsed_config['module_type']} series")
    print(f"Address:         {parsed_config['address_hex']} ({parsed_config['address']})")
    print(f"Network ID:      {parsed_config['network_id_hex']} ({parsed_config['network_id']})")
    print(f"Channel:         {parsed_config['channel']} ({parsed_config['frequency_mhz']:.3f} MHz)")
    print("-"*60)
    print(f"UART Baud:       {parsed_config['uart_baud_rate']} bps")
    print(f"UART Parity:     {parsed_config['uart_parity']}")
    print(f"Air Data Rate:   {parsed_config['air_rate']} bps")
    print(f"Sub-Packet:      {parsed_config['sub_packet_size']} bytes")
    print("-"*60)
    print(f"TX Power:        {parsed_config['transmit_power']}")
    print(f"RSSI Ambient:    {'Enabled' if parsed_config['rssi_ambient_enable'] else 'Disabled'}")
    print(f"RSSI Byte:       {'Enabled' if parsed_config['rssi_byte_enable'] else 'Disabled'}")
    print("-"*60)
    print(f"Trans Mode:      {parsed_config['transmission_mode']}")
    print(f"Relay/Repeater:  {'Enabled' if parsed_config['relay_enable'] else 'Disabled'}")
    print(f"LBT:             {'Enabled' if parsed_config['lbt_enable'] else 'Disabled'}")
    print(f"WOR Mode:        {parsed_config['wor_mode']}")
    print(f"WOR Period:      {parsed_config['wor_period_ms']} ms")
    print("-"*60)
    print(f"Raw Config:      {parsed_config['raw_hex']}")
    print("="*60)


def main():
    """Main entry point for the E22 configuration tool"""
    parser = argparse.ArgumentParser(
        description="E22 LoRa Module Configuration Tool (Official Ebyte Register Mapping)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get version information
  %(prog)s --version

  # Read current configuration
  %(prog)s --port /dev/ttyUSB0

  # Set module address and channel
  %(prog)s --address 0x1234 --channel 21

  # Configure for E22-900 series
  %(prog)s --model 900 --address 0x0001 --channel 18 --power 33dBm

  # Configure for E22-400 series
  %(prog)s --model 400 --address 0x0001 --channel 23 --power 22dBm
        """
    )

    parser.add_argument("--port", default="/dev/ttyUSB0",
                       help="Serial port (default: /dev/ttyUSB0)")
    parser.add_argument("--model", choices=["400", "900", "auto"], default="auto",
                       help="Module type: 400 for E22-400 (433MHz), 900 for E22-900 (868/915MHz), auto for autodetect")
    parser.add_argument("--version", action="store_true",
                       help="Display module firmware version and exit")
    parser.add_argument("--address", type=lambda x: int(x, 0),
                       help="Set address (0-65535, e.g., 0x1234)")
    parser.add_argument("--network-id", type=lambda x: int(x, 0),
                       help="Set network ID (0-255, e.g., 0x00)")
    parser.add_argument("--channel", type=int,
                       help="Set channel (0-83)")
    parser.add_argument("--air-rate",
                       choices=["2.4k", "4.8k", "9.6k", "19.2k", "38.4k", "62.5k"],
                       help="Set air data rate")
    parser.add_argument("--baud-rate",
                       choices=["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"],
                       help="Set UART baud rate")
    parser.add_argument("--parity", choices=["8N1", "8O1", "8E1"],
                       help="Set parity mode")
    parser.add_argument("--power",
                       help="Set transmit power (e.g., 33dBm, 30dBm, 27dBm, 24dBm for E22-900)")
    parser.add_argument("--sub-packet", choices=["240", "128", "64", "32"],
                       help="Set sub-packet size in bytes")
    parser.add_argument("--rssi-ambient", choices=["0", "1"],
                       help="Enable RSSI ambient noise (0: Disable, 1: Enable)")
    parser.add_argument("--rssi-byte", choices=["0", "1"],
                       help="Enable RSSI byte output (0: Disable, 1: Enable)")
    parser.add_argument("--fixed-transmission", choices=["0", "1"],
                       help="Transmission mode (0: Transparent, 1: Fixed-point)")
    parser.add_argument("--relay", choices=["0", "1"],
                       help="Relay/repeater function (0: Disable, 1: Enable)")
    parser.add_argument("--lbt", choices=["0", "1"],
                       help="Listen Before Talk (0: Disable, 1: Enable)")
    parser.add_argument("--wor-mode", choices=["0", "1"],
                       help="WOR mode (0: Receiver, 1: Transmitter)")
    parser.add_argument("--wor-period", type=int, choices=[500, 1000, 1500, 2000, 2500, 3000, 3500, 4000],
                       help="WOR period in milliseconds")
    parser.add_argument("--write-key", nargs=2, type=lambda x: int(x, 16),
                       help="Write encryption key (high_byte low_byte in hex)")
    parser.add_argument("--read-product-info", action="store_true",
                       help="Read product information")
    parser.add_argument("--debug", action="store_true",
                       help="Enable debug logging")

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Determine baud rate to use
        baud_rate_to_use = int(args.baud_rate) if args.baud_rate else 9600

        with E22Module(args.port, baudrate=baud_rate_to_use, timeout=1, module_type=args.model) as e22:

            # Handle --version flag
            if args.version:
                version_info = e22.get_version()
                if version_info:
                    print("\nE22 Module Version Information:")
                    print(f"  Model:    0x{version_info['model']:02X}")
                    print(f"  Version:  0x{version_info['version']:02X}")
                    print(f"  Features: 0x{version_info['features']:02X}")
                    if 'extra' in version_info:
                        print(f"  Extra:    0x{version_info['extra']:02X}")
                    print(f"  Raw:      {version_info['raw']}")
                else:
                    print("\nNote: Version command (C3 C3 C3) not supported by this module.")
                    print("This is normal for many E22 modules.")
                return 0

            # Handle encryption key writing
            if args.write_key:
                e22.write_encryption_keys(*args.write_key)
                print(f"\nEncryption keys written: 0x{args.write_key[0]:02X} 0x{args.write_key[1]:02X}")

            # Handle product info reading
            if args.read_product_info:
                product_info = e22.read_product_info()
                print("\nProduct Information (PIDs):")
                print(f"  Raw: {product_info.hex(' ').upper()}")

            # Read current configuration
            current_config = e22.read_config()
            parsed_config = e22.parse_config(current_config)

            # Check if any configuration changes requested
            config_changed = any([
                args.address, args.network_id, args.channel, args.air_rate,
                args.baud_rate, args.parity, args.power, args.sub_packet,
                args.rssi_ambient, args.rssi_byte, args.fixed_transmission,
                args.relay, args.lbt, args.wor_mode, args.wor_period
            ])

            if config_changed:
                # Prepare new configuration
                new_address = args.address if args.address is not None else parsed_config['address']
                new_network_id = args.network_id if args.network_id is not None else parsed_config['network_id']
                new_channel = args.channel if args.channel is not None else parsed_config['channel']
                new_air_rate = args.air_rate if args.air_rate else parsed_config['air_rate']
                new_baud_rate = args.baud_rate if args.baud_rate else parsed_config['uart_baud_rate']
                new_parity = args.parity if args.parity else parsed_config['uart_parity']
                new_power = args.power if args.power else parsed_config['transmit_power']
                new_sub_packet = args.sub_packet if args.sub_packet else parsed_config['sub_packet_size']
                new_rssi_ambient = bool(int(args.rssi_ambient)) if args.rssi_ambient else parsed_config['rssi_ambient_enable']
                new_rssi_byte = bool(int(args.rssi_byte)) if args.rssi_byte else parsed_config['rssi_byte_enable']
                new_fixed = bool(int(args.fixed_transmission)) if args.fixed_transmission else (parsed_config['transmission_mode'] == 'fixed-point')
                new_relay = bool(int(args.relay)) if args.relay else parsed_config['relay_enable']
                new_lbt = bool(int(args.lbt)) if args.lbt else parsed_config['lbt_enable']
                new_wor_tx = bool(int(args.wor_mode)) if args.wor_mode else (parsed_config['wor_mode'] == 'transmitter')
                new_wor_period = args.wor_period if args.wor_period else parsed_config['wor_period_ms']

                # Create new configuration
                new_config = E22Module.create_config(
                    address=new_address,
                    network_id=new_network_id,
                    channel=new_channel,
                    air_rate=new_air_rate,
                    baud_rate=new_baud_rate,
                    parity=new_parity,
                    power=new_power,
                    sub_packet_size=new_sub_packet,
                    rssi_ambient_enable=new_rssi_ambient,
                    rssi_byte_enable=new_rssi_byte,
                    fixed_transmission=new_fixed,
                    relay_enable=new_relay,
                    lbt_enable=new_lbt,
                    wor_transmitter=new_wor_tx,
                    wor_period_ms=new_wor_period
                )

                # Write configuration
                e22.write_config(new_config)
                print("\n✓ Configuration updated successfully")

                # If baud rate was changed, reconnect
                if args.baud_rate:
                    e22.close()
                    time.sleep(0.5)
                    e22.baudrate = int(args.baud_rate)
                    e22.open()

                # Re-read configuration to verify
                current_config = e22.read_config()
                parsed_config = e22.parse_config(current_config)

            # Print current configuration
            print_config(parsed_config)

            return 0

    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
