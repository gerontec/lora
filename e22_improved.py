#!/usr/bin/python3
"""
Improved E22 LoRa Module Configuration Tool
Includes proper version information handling and class-based architecture
"""
import serial
import time
import argparse
import logging
import sys

# Set up logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')


class E22Module:
    """Class to handle E22 LoRa module communication and configuration"""

    def __init__(self, port, baudrate=9600, timeout=1):
        """Initialize the E22 module connection

        Args:
            port: Serial port path (e.g., /dev/ttyUSB0)
            baudrate: Baud rate for serial communication
            timeout: Serial timeout in seconds
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None

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
        """Read current module configuration

        Returns:
            9 bytes of configuration data
        """
        command = bytes([0xC1, 0x00, 0x09])
        response = self.send_command(command)
        if len(response) < 12:
            raise ValueError(f"Unexpected response length or format: {response.hex()}")
        return response[3:12]  # Return 9 bytes of configuration data

    def write_config(self, config):
        """Write configuration to module

        Args:
            config: List of 9 configuration bytes

        Returns:
            9 bytes of confirmed configuration
        """
        command = bytes([0xC0, 0x00, 0x09] + config)
        response = self.send_command(command)
        if response[0:3] != bytes([0xC1, 0x00, 0x09]):
            raise ValueError(f"Failed to write configuration: {response.hex()}")
        return response[3:12]

    def write_encryption_keys(self, key_high, key_low):
        """Write encryption keys to module

        Args:
            key_high: High byte of encryption key
            key_low: Low byte of encryption key
        """
        command = bytes([0xC0, 0x00, 0x02, key_high, key_low])
        response = self.send_command(command)
        if response[0:3] != bytes([0xC1, 0x00, 0x02]):
            raise ValueError(f"Failed to write encryption keys: {response.hex()}")

    def read_product_info(self):
        """Read product information from module

        Returns:
            7 bytes of product information
        """
        command = bytes([0xC1, 0x80, 0x07])
        response = self.send_command(command)
        if len(response) < 10:
            raise ValueError(f"Unexpected response length or format for product info: {response.hex()}")
        return response[3:10]  # Return 7 bytes of product information

    def get_version(self):
        """Get firmware version information from module

        The version command (0xC3, 0xC3, 0xC3) typically returns 3-4 bytes:
        - Byte 0: Model
        - Byte 1: Version
        - Byte 2: Features
        - Byte 3: (optional) Additional info

        Returns:
            Dictionary with version information
        """
        command = bytes([0xC3, 0xC3, 0xC3])
        response = self.send_command(command)

        # Version response can be 3 or 4 bytes
        if len(response) < 3:
            raise ValueError(f"Invalid version response length: {len(response)}. Expected at least 3 bytes, got {response.hex()}")

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

        current_noise_dbm = - (256 - current_noise_rssi)
        last_received_dbm = - (256 - last_received_rssi)

        return {
            "Current Noise RSSI": current_noise_dbm,
            "Last Received RSSI": last_received_dbm
        }

    @staticmethod
    def parse_config(config):
        """Parse configuration bytes into readable format

        Args:
            config: 9 bytes of configuration data

        Returns:
            Dictionary with parsed configuration
        """
        addh, addl, netid, reg0, reg1, reg2, reg3, reg4, reg5 = config
        address = (addh << 8) | addl
        network_address = netid
        channel = reg2
        air_rate_code = reg0 & 0x07
        air_rates = ["0.3k", "1.2k", "2.4k", "4.8k", "9.6k", "19.2k", "38.4k", "62.5k"]
        air_rate = air_rates[air_rate_code] if air_rate_code < len(air_rates) else "Unknown"
        baud_rate_code = (reg0 >> 5) & 0x07
        baud_rates = ["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"]
        baud_rate = baud_rates[baud_rate_code] if baud_rate_code < len(baud_rates) else "Unknown"
        parity_code = (reg0 >> 3) & 0x03
        parities = ["8N1", "8O1", "8E1", "8N1"]
        parity = parities[parity_code]
        power_code = reg1 & 0x03
        powers = ["13dBm", "18dBm", "22dBm", "27dBm"]
        power = powers[power_code] if power_code < len(powers) else "Unknown"
        fixed_transmission = "Fixed-point" if reg3 & 0x40 else "Transparent"
        relay_function = "Enabled" if reg3 & 0x20 else "Disabled"
        lbt_enable = "Enabled" if reg3 & 0x10 else "Disabled"
        rssi_enable = "Enabled" if reg1 & 0x20 else "Disabled"
        noise_enable = "Enabled" if reg3 & 0x80 else "Disabled"

        return {
            "Address": f"0x{address:04X}",
            "Network Address": f"0x{network_address:02X}",
            "Channel": channel,
            "Air Rate": air_rate,
            "Baud Rate": baud_rate,
            "Parity": parity,
            "Transmitting Power": power,
            "Fixed Transmission": fixed_transmission,
            "Relay Function": relay_function,
            "LBT Enable": lbt_enable,
            "RSSI Enable": rssi_enable,
            "Noise Enable": noise_enable
        }

    @staticmethod
    def create_config(address, network_address, channel, air_rate, baud_rate, parity,
                     power, fixed_transmission, relay_function, lbt_enable, rssi_enable,
                     noise_enable="0"):
        """Create configuration bytes from parameters

        Args:
            address: Module address (0-65535)
            network_address: Network ID (0-255)
            channel: Channel number (0-83)
            air_rate: Air data rate (e.g., "2.4k")
            baud_rate: UART baud rate (e.g., "9600")
            parity: Parity mode (e.g., "8N1")
            power: Transmit power (e.g., "22dBm")
            fixed_transmission: "1" for fixed-point, "0" for transparent
            relay_function: "1" to enable relay, "0" to disable
            lbt_enable: "1" to enable LBT, "0" to disable
            rssi_enable: "1" to enable RSSI, "0" to disable
            noise_enable: "1" to enable noise reading, "0" to disable

        Returns:
            List of 9 configuration bytes
        """
        addh = (address >> 8) & 0xFF
        addl = address & 0xFF
        netid = network_address

        air_rates = {"0.3k": 0, "1.2k": 1, "2.4k": 2, "4.8k": 3, "9.6k": 4, "19.2k": 5, "38.4k": 6, "62.5k": 7}
        baud_rates = {"1200": 0, "2400": 1, "4800": 2, "9600": 3, "19200": 4, "38400": 5, "57600": 6, "115200": 7}
        parities = {"8N1": 0, "8O1": 1, "8E1": 2}
        powers = {"13dBm": 0, "18dBm": 1, "22dBm": 2, "27dBm": 3}

        reg0 = (baud_rates[baud_rate] << 5) | (parities[parity] << 3) | air_rates[air_rate]
        reg1 = 0xE0 | powers[power]

        if rssi_enable == "1":
            reg1 |= 0x20
        else:
            reg1 &= ~0x20

        reg2 = channel
        reg3 = 0x80

        if noise_enable == "1":
            reg3 |= 0x80
        else:
            reg3 &= ~0x80

        if fixed_transmission == "1":
            reg3 |= 0x40
        else:
            reg3 &= ~0x40

        if relay_function == "1":
            reg3 |= 0x20
        else:
            reg3 &= ~0x20

        if lbt_enable == "1":
            reg3 |= 0x10
        else:
            reg3 &= ~0x10

        reg4 = 0
        reg5 = 0

        return [addh, addl, netid, reg0, reg1, reg2, reg3, reg4, reg5]


def format_version_info(version_info):
    """Format version information for display

    Args:
        version_info: Dictionary with version information

    Returns:
        Formatted string
    """
    lines = []
    lines.append("E22 Module Version Information:")
    lines.append(f"  Model:    0x{version_info['model']:02X}")
    lines.append(f"  Version:  0x{version_info['version']:02X}")
    lines.append(f"  Features: 0x{version_info['features']:02X}")
    if 'extra' in version_info:
        lines.append(f"  Extra:    0x{version_info['extra']:02X}")
    lines.append(f"  Raw:      {version_info['raw']}")
    return "\n".join(lines)


def print_config(parsed_config, raw_config):
    """Print module configuration

    Args:
        parsed_config: Dictionary with parsed configuration
        raw_config: Raw configuration bytes
    """
    print("\nE22 Module Configuration:")
    for key, value in parsed_config.items():
        print(f"  {key}: {value}")
    print(f"  Raw Config: {raw_config.hex(' ').upper()}")


def print_product_info(product_info):
    """Print product information

    Args:
        product_info: Raw product information bytes
    """
    print("\nProduct Information:")
    print(f"  Raw Product Info: {product_info.hex(' ').upper()}")


def main():
    """Main entry point for the E22 configuration tool"""
    parser = argparse.ArgumentParser(
        description="Read/Write configuration for E22 LoRa module",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get version information
  %(prog)s --version

  # Read current configuration
  %(prog)s --port /dev/ttyUSB0

  # Set module address and channel
  %(prog)s --address 0x1234 --channel 21

  # Configure all parameters
  %(prog)s --address 0x1234 --network-address 0x00 --channel 21 \\
           --air-rate 2.4k --baud-rate 9600 --parity 8N1 --power 22dBm \\
           --fixed-transmission 1 --relay-function 0 --lbt-enable 0 \\
           --rssi-enable 1
        """
    )

    parser.add_argument("--port", default="/dev/ttyUSB0",
                       help="Serial port (default: /dev/ttyUSB0)")
    parser.add_argument("--version", action="store_true",
                       help="Display module firmware version and exit")
    parser.add_argument("--address", type=lambda x: int(x, 0),
                       help="Set address (e.g., 0x1234)")
    parser.add_argument("--network-address", type=lambda x: int(x, 0), default=None,
                       help="Set network address (e.g., 0x00)")
    parser.add_argument("--channel", type=int,
                       help="Set channel (0-83)")
    parser.add_argument("--air-rate",
                       choices=["0.3k", "1.2k", "2.4k", "4.8k", "9.6k", "19.2k", "38.4k", "62.5k"],
                       help="Set air rate")
    parser.add_argument("--baud-rate",
                       choices=["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"],
                       help="Set baud rate")
    parser.add_argument("--parity", choices=["8N1", "8O1", "8E1"],
                       help="Set parity")
    parser.add_argument("--power", choices=["13dBm", "18dBm", "22dBm", "27dBm"],
                       help="Set transmitting power")
    parser.add_argument("--fixed-transmission", choices=["0", "1"],
                       help="Set fixed-point transmission (0: Transparent, 1: Fixed-point)")
    parser.add_argument("--relay-function", choices=["0", "1"],
                       help="Set relay function (0: Disable, 1: Enable)")
    parser.add_argument("--lbt-enable", choices=["0", "1"],
                       help="Set LBT enable (0: Disable, 1: Enable)")
    parser.add_argument("--rssi-enable", choices=["0", "1"],
                       help="Enable RSSI reading (0: Disable, 1: Enable)")
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

        with E22Module(args.port, baudrate=baud_rate_to_use, timeout=1) as e22:
            # Handle --version flag
            if args.version:
                version_info = e22.get_version()
                print(format_version_info(version_info))
                return 0

            # Handle encryption key writing
            if args.write_key:
                e22.write_encryption_keys(*args.write_key)
                print(f"Encryption keys written: 0x{args.write_key[0]:02X} 0x{args.write_key[1]:02X}")

            # Handle product info reading
            if args.read_product_info or not any([
                args.address, args.network_address, args.channel, args.air_rate,
                args.baud_rate, args.parity, args.power, args.fixed_transmission,
                args.relay_function, args.lbt_enable, args.rssi_enable, args.write_key
            ]):
                product_info = e22.read_product_info()
                print_product_info(product_info)

            # Read current configuration
            current_config = e22.read_config()
            parsed_config = E22Module.parse_config(current_config)

            # Handle configuration updates
            if any([
                args.address, args.network_address, args.channel, args.air_rate,
                args.baud_rate, args.parity, args.power, args.fixed_transmission,
                args.relay_function, args.lbt_enable, args.rssi_enable
            ]):
                # Update parsed config with new values
                if args.address is not None:
                    parsed_config['Address'] = f"0x{args.address:04X}"
                if args.network_address is not None:
                    parsed_config['Network Address'] = f"0x{args.network_address:02X}"
                if args.channel is not None:
                    parsed_config['Channel'] = args.channel
                if args.air_rate is not None:
                    parsed_config['Air Rate'] = args.air_rate
                if args.baud_rate is not None:
                    parsed_config['Baud Rate'] = args.baud_rate
                if args.parity is not None:
                    parsed_config['Parity'] = args.parity
                if args.power is not None:
                    parsed_config['Transmitting Power'] = args.power
                if args.fixed_transmission is not None:
                    parsed_config['Fixed Transmission'] = "Fixed-point" if args.fixed_transmission == "1" else "Transparent"
                if args.relay_function is not None:
                    parsed_config['Relay Function'] = "Enabled" if args.relay_function == "1" else "Disabled"
                if args.lbt_enable is not None:
                    parsed_config['LBT Enable'] = "Enabled" if args.lbt_enable == "1" else "Disabled"
                if args.rssi_enable is not None:
                    parsed_config['RSSI Enable'] = "Enabled" if args.rssi_enable == "1" else "Disabled"

                # Create new configuration
                new_config = E22Module.create_config(
                    int(parsed_config['Address'], 16),
                    int(parsed_config['Network Address'], 16),
                    parsed_config['Channel'],
                    parsed_config['Air Rate'],
                    parsed_config['Baud Rate'],
                    parsed_config['Parity'],
                    parsed_config['Transmitting Power'],
                    "1" if parsed_config['Fixed Transmission'] == "Fixed-point" else "0",
                    "1" if parsed_config['Relay Function'] == "Enabled" else "0",
                    "1" if parsed_config['LBT Enable'] == "Enabled" else "0",
                    "1" if parsed_config['RSSI Enable'] == "Enabled" else "0"
                )

                # Write configuration
                e22.write_config(new_config)
                print("Configuration updated successfully.")

                # If baud rate was changed, reconnect with new baud rate
                if args.baud_rate:
                    e22.close()
                    time.sleep(0.5)
                    baud_rate_to_use = int(args.baud_rate)
                    e22.baudrate = baud_rate_to_use
                    e22.open()

                # Re-read configuration to verify
                current_config = e22.read_config()
                parsed_config = E22Module.parse_config(current_config)
            else:
                if not args.write_key:
                    print("No configuration arguments provided. Showing current configuration.")

            # Print current configuration
            print_config(parsed_config, current_config)

            return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
