#!/usr/bin/env python3
###############################################################################
# Improved Python class for EBYTE E22 Series LoRa modules
# Based on loraE22 by Matthias Prinke and Heinz-Bernd Eggenstein
# Improved with official Ebyte documentation and bug fixes
#
# Changes from original:
# - Fixed hardcoded sub-packet size (now configurable)
# - Added encryption key support (REG4/REG5)
# - Fixed LBT typo ('disabe' -> 'disable')
# - Added model variant support (T20/T22/T27/T30 with different power levels)
# - CPython compatibility (not just MicroPython)
# - Improved validation and error handling
# - Better documentation based on official Ebyte E22 datasheet
#
# Based on official E22 documentation:
# https://www.cdebyte.com/ (Ebyte official datasheets)
# https://www.fr-ebyte.com/Uploadfiles/Files/2024-1-9/2024191548299095.pdf
#
###############################################################################

import serial
import time
import json
from typing import Optional, Dict, Any, Tuple

class EbyteE22:
    """
    Class to interface with EBYTE E22 Series LoRa modules via serial UART.

    Supports E22 modules based on SEMTECH SX1262/SX1268 chipsets:
    - 400 MHz (410.125~493.125 MHz)
    - 900 MHz (850.125~930.125 MHz)

    Module variants:
    - T20/T22: 22 dBm max TX power (22/17/13/10 dBm)
    - T27: 27 dBm max TX power (27/24/21/18 dBm)
    - T30: 30 dBm max TX power (30/27/24/21 dBm)
    """

    # UART parity strings for REG0 bits 4-3
    PARSTR = { '8N1': '00', '8O1': '01', '8E1': '10' }
    PARINV = { v: k for k, v in PARSTR.items() }

    # UART baudrate for REG0 bits 7-5
    BAUDRATE = {
        1200: '000', 2400: '001', 4800: '010', 9600: '011',
        19200: '100', 38400: '101', 57600: '110', 115200: '111'
    }
    BAUDRINV = { v: k for k, v in BAUDRATE.items() }

    # Air data rate for REG0 bits 2-0
    DATARATE = {
        '0.3k': '000', '1.2k': '001', '2.4k': '010', '4.8k': '011',
        '9.6k': '100', '19.2k': '101', '38.4k': '110', '62.5k': '111'
    }
    DATARINV = { v: k for k, v in DATARATE.items() }

    # Commands
    CMDS = {
        'setConfigPwrDwnSave': 0xC0,      # Write config with save
        'getConfig': 0xC1,                 # Read config
        'setConfigPwrDwnNoSave': 0xC2,    # Write config without save
        'getVersion': 0xC3,                # Get version info
        'reset': 0xC4                      # Reset module
    }

    # Sub-packet setting for REG1 bits 7-6
    SUBPINV = { '240B': '00', '128B': '01', '64B': '10', '32B': '11' }
    SUBPCKT = { 0b00: '240B', 0b01: '128B', 0b10: '64B', 0b11: '32B' }

    # Transmitting power for REG1 bits 1-0
    # IMPORTANT: 0b00 is MAXIMUM power, 0b11 is MINIMUM power!
    TXPOWER_T20_T22 = {
        0b00: '22dBm', 0b01: '17dBm', 0b10: '13dBm', 0b11: '10dBm'
    }
    TXPOWER_T27 = {
        0b00: '27dBm', 0b01: '24dBm', 0b10: '21dBm', 0b11: '18dBm'
    }
    TXPOWER_T30 = {
        0b00: '30dBm', 0b01: '27dBm', 0b10: '24dBm', 0b11: '21dBm'
    }

    # Inverse mappings for power
    TXPWRINV_T20_T22 = { v: k for k, v in TXPOWER_T20_T22.items() }
    TXPWRINV_T27 = { v: k for k, v in TXPOWER_T27.items() }
    TXPWRINV_T30 = { v: k for k, v in TXPOWER_T30.items() }

    # REG3 bit mappings
    RSSI = { 0: 'disable', 1: 'enable' }
    TRANSMODE = { 0: 'transparent', 1: 'fixed' }
    REPEATER = { 0: 'disable', 1: 'enable' }
    LBT = { 0: 'disable', 1: 'enable' }  # Fixed typo from original
    WORCTRL = { 0: 'WOR receiver', 1: 'WOR transmitter' }

    # WOR wake-up times for REG3 bits 2-0
    WUTIME = {
        0b000: '500ms', 0b001: '1000ms', 0b010: '1500ms', 0b011: '2000ms',
        0b100: '2500ms', 0b101: '3000ms', 0b110: '3500ms', 0b111: '4000ms'
    }
    WUTIMEINV = { v: k for k, v in WUTIME.items() }

    def __init__(
        self,
        port: str = '/dev/ttyUSB0',
        model: str = '900T22D',
        baudrate: int = 9600,
        parity: str = '8N1',
        air_datarate: str = '2.4k',
        address: int = 0x0000,
        netid: int = 0x00,
        channel: int = 0x06,
        sub_packet: str = '240B',
        rssi_ambient_noise: bool = False,
        rssi_enable: bool = False,
        transmode: int = 0,
        repeater: bool = False,
        lbt: bool = False,
        wor_control: int = 0,
        wor_period: str = '2000ms',
        tx_power: str = '22dBm',
        crypt_h: int = 0x00,
        crypt_l: int = 0x00,
        debug: bool = False
    ):
        """
        Initialize EBYTE E22 LoRa module.

        Args:
            port: Serial port device (e.g., '/dev/ttyUSB0')
            model: E22 model variant (e.g., '900T22D', '400T30S')
            baudrate: UART baudrate for serial communication
            parity: UART parity ('8N1', '8O1', '8E1')
            air_datarate: Air data rate ('0.3k' to '62.5k')
            address: Module address (0x0000-0xFFFF)
            netid: Network ID (0x00-0xFF)
            channel: Channel number (0-80 for 900MHz, 0-83 for some models)
            sub_packet: Sub-packet size ('240B', '128B', '64B', '32B')
            rssi_ambient_noise: Enable ambient noise RSSI measurement
            rssi_enable: Enable RSSI byte in received data
            transmode: Transmission mode (0=transparent, 1=fixed)
            repeater: Enable repeater/relay function
            lbt: Enable Listen Before Talk
            wor_control: WOR control (0=receiver, 1=transmitter)
            wor_period: WOR wake-up period ('500ms' to '4000ms')
            tx_power: Transmitting power (depends on model variant)
            crypt_h: Encryption key high byte (0x00-0xFF)
            crypt_l: Encryption key low byte (0x00-0xFF)
            debug: Enable debug output
        """
        self.port = port
        self.debug = debug
        self.ser: Optional[serial.Serial] = None

        # Detect model variant for power mapping
        self.model = model
        if 'T30' in model.upper():
            self.power_map = self.TXPOWER_T30
            self.power_inv = self.TXPWRINV_T30
        elif 'T27' in model.upper():
            self.power_map = self.TXPOWER_T27
            self.power_inv = self.TXPWRINV_T27
        else:
            # T20/T22 or default
            self.power_map = self.TXPOWER_T20_T22
            self.power_inv = self.TXPWRINV_T20_T22

        # Configuration dictionary
        self.config = {
            'model': model,
            'port': port,
            'baudrate': baudrate,
            'parity': parity,
            'datarate': air_datarate,
            'address': address,
            'netid': netid,
            'channel': channel,
            'subpckt': sub_packet,  # Fixed: was missing in original
            'amb_noise': 1 if rssi_ambient_noise else 0,
            'rssi': 1 if rssi_enable else 0,
            'transmode': transmode,
            'repeater': 1 if repeater else 0,
            'lbt': 1 if lbt else 0,
            'worctrl': wor_control,
            'wutime': self.WUTIMEINV.get(wor_period, 0b011),  # Default 2000ms
            'txpower': self.power_inv.get(tx_power, 0b00),  # Default max power
            'crypt_h': crypt_h,
            'crypt_l': crypt_l
        }

        # Validate configuration
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate configuration parameters."""
        if self.config['baudrate'] not in self.BAUDRATE:
            raise ValueError(f"Invalid baudrate: {self.config['baudrate']}")

        if self.config['parity'] not in self.PARSTR:
            raise ValueError(f"Invalid parity: {self.config['parity']}")

        if self.config['datarate'] not in self.DATARATE:
            raise ValueError(f"Invalid air datarate: {self.config['datarate']}")

        if self.config['subpckt'] not in self.SUBPINV:
            raise ValueError(f"Invalid sub-packet size: {self.config['subpckt']}")

        if not 0 <= self.config['address'] <= 0xFFFF:
            raise ValueError(f"Invalid address: {self.config['address']}")

        if not 0 <= self.config['channel'] <= 83:
            raise ValueError(f"Invalid channel: {self.config['channel']}")

    def connect(self, auto_detect: bool = True) -> bool:
        """
        Open serial connection to E22 module.

        Args:
            auto_detect: If True, automatically detect module model

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.config['baudrate'],
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            time.sleep(0.1)
            if self.debug:
                print(f"✓ Connected to {self.port} at {self.config['baudrate']} baud")

            # Auto-detect module model
            if auto_detect:
                try:
                    version_info = self.get_version()

                    # Only update model if we got valid frequency info
                    if version_info.get('supported', False):
                        freq = version_info.get('frequency', 'Unknown')

                        if self.debug:
                            print(f"✓ Detected module frequency: {freq}")

                        # Update model in config based on detected frequency
                        if '400' in freq or '433' in freq or '470' in freq:
                            # It's a 400MHz variant
                            if 'T30' in self.model.upper():
                                self.config['model'] = f"400T30S"
                            elif 'T27' in self.model.upper():
                                self.config['model'] = f"400T27S"
                            else:
                                self.config['model'] = f"400T22S"
                        elif '868' in freq or '915' in freq or '900' in freq:
                            # It's a 900MHz variant
                            if 'T30' in self.model.upper():
                                self.config['model'] = f"900T30S"
                            elif 'T27' in self.model.upper():
                                self.config['model'] = f"900T27S"
                            else:
                                self.config['model'] = f"900T22D"

                        if self.debug:
                            print(f"✓ Updated model to: {self.config['model']}")
                    else:
                        if self.debug:
                            print(f"⚠ Auto-detection not supported by this module")
                            print(f"  Using configured model: {self.config['model']}")

                except Exception as e:
                    if self.debug:
                        print(f"⚠ Auto-detection failed: {e}, using default model")

            return True
        except serial.SerialException as e:
            print(f"✗ Error connecting to {self.port}: {e}")
            return False

    def disconnect(self) -> None:
        """Close serial connection."""
        if self.ser and self.ser.is_open:
            self.ser.close()
            if self.debug:
                print("✓ Disconnected from serial port")

    def _send_command(self, command: bytes, wait_time: float = 0.1) -> bytes:
        """
        Send command to module and read response.

        Args:
            command: Command bytes to send
            wait_time: Time to wait for response (seconds)

        Returns:
            Response bytes from module
        """
        if not self.ser or not self.ser.is_open:
            raise RuntimeError("Serial port not open")

        self.ser.reset_input_buffer()
        self.ser.write(command)

        if self.debug:
            print(f"TX: {command.hex(' ').upper()}")

        time.sleep(wait_time)
        response = self.ser.read(100)

        if self.debug:
            print(f"RX: {response.hex(' ').upper()}")

        return response

    def encode_config(self, save: bool = True) -> bytes:
        """
        Encode configuration dictionary to bytes for writing to module.

        Args:
            save: If True, use C0 (save), otherwise C2 (no save)

        Returns:
            Configuration command bytes
        """
        message = bytearray()

        # Command header
        if save:
            message.append(self.CMDS['setConfigPwrDwnSave'])
        else:
            message.append(self.CMDS['setConfigPwrDwnNoSave'])

        # Starting address
        message.append(0x00)

        # Length (9 bytes: ADDH, ADDL, NETID, REG0-5)
        message.append(0x09)

        # ADDH (address high byte)
        message.append(self.config['address'] // 256)

        # ADDL (address low byte)
        message.append(self.config['address'] % 256)

        # NETID (network ID)
        message.append(self.config['netid'])

        # REG0: UART baud (7-5) | Parity (4-3) | Air rate (2-0)
        reg0_bits = '0b'
        reg0_bits += self.BAUDRATE[self.config['baudrate']]
        reg0_bits += self.PARSTR[self.config['parity']]
        reg0_bits += self.DATARATE[self.config['datarate']]
        message.append(int(reg0_bits, 2))

        # REG1: Sub-packet (7-6) | Ambient noise (5) | Reserved (4-2) | TX power (1-0)
        reg1_bits = '0b'
        reg1_bits += self.SUBPINV[self.config['subpckt']]  # Fixed: now configurable
        reg1_bits += str(self.config['amb_noise'])
        reg1_bits += '000'  # Reserved
        reg1_bits += f"{self.config['txpower']:02b}"
        message.append(int(reg1_bits, 2))

        # REG2: Channel
        message.append(self.config['channel'])

        # REG3: RSSI (7) | TransMode (6) | Repeater (5) | LBT (4) | WOR ctrl (3) | WOR time (2-0)
        reg3_bits = '0b'
        reg3_bits += str(self.config['rssi'])
        reg3_bits += str(self.config['transmode'])
        reg3_bits += str(self.config['repeater'])
        reg3_bits += str(self.config['lbt'])
        reg3_bits += str(self.config['worctrl'])
        reg3_bits += f"{self.config['wutime']:03b}"
        message.append(int(reg3_bits, 2))

        # REG4: Encryption key high byte (NEW!)
        message.append(self.config['crypt_h'])

        # REG5: Encryption key low byte (NEW!)
        message.append(self.config['crypt_l'])

        return bytes(message)

    def decode_config(self, response: bytes) -> Dict[str, Any]:
        """
        Decode configuration response from module.

        Args:
            response: Response bytes from module

        Returns:
            Configuration dictionary
        """
        if len(response) < 12:
            raise ValueError(f"Invalid response length: {len(response)}")

        if response[0] != 0xC1:
            raise ValueError(f"Invalid response header: 0x{response[0]:02X}")

        config = {}

        # ADDH and ADDL
        config['address'] = (response[3] << 8) | response[4]

        # NETID
        config['netid'] = response[5]

        # REG0
        reg0 = response[6]
        baud_code = (reg0 >> 5) & 0x07
        parity_code = (reg0 >> 3) & 0x03
        air_code = reg0 & 0x07

        config['baudrate'] = self.BAUDRINV.get(f"{baud_code:03b}", 9600)
        config['parity'] = self.PARINV.get(f"{parity_code:02b}", '8N1')
        config['datarate'] = self.DATARINV.get(f"{air_code:03b}", '2.4k')

        # REG1
        reg1 = response[7]
        subpckt_code = (reg1 >> 6) & 0x03
        config['subpckt'] = self.SUBPCKT.get(subpckt_code, '240B')
        config['amb_noise'] = (reg1 >> 5) & 0x01
        config['txpower'] = reg1 & 0x03

        # REG2
        config['channel'] = response[8]

        # REG3
        reg3 = response[9]
        config['rssi'] = (reg3 >> 7) & 0x01
        config['transmode'] = (reg3 >> 6) & 0x01
        config['repeater'] = (reg3 >> 5) & 0x01
        config['lbt'] = (reg3 >> 4) & 0x01
        config['worctrl'] = (reg3 >> 3) & 0x01
        config['wutime'] = reg3 & 0x07

        # REG4 & REG5 (encryption keys)
        if len(response) >= 12:
            config['crypt_h'] = response[10]
            config['crypt_l'] = response[11]
        else:
            config['crypt_h'] = 0x00
            config['crypt_l'] = 0x00

        return config

    def get_version(self) -> Dict[str, Any]:
        """
        Read module version and model information.

        Returns:
            Dictionary with model, version, and frequency info
            Returns None values if module doesn't support version command
        """
        command = bytes([self.CMDS['getVersion'], 0x00, 0x00])
        response = self._send_command(command, wait_time=0.2)

        if len(response) < 3:
            if self.debug:
                print(f"⚠ Version command not supported or module not responding")
                print(f"  Response: {response.hex(' ').upper() if response else 'empty'}")
            # Return empty version info
            return {
                'header': None,
                'model': None,
                'version': None,
                'features': None,
                'frequency': 'Unknown',
                'supported': False
            }

        # Some E22 modules don't fully support getVersion command
        version_info = {
            'header': response[0] if len(response) > 0 else None,
            'model': response[1] if len(response) > 1 else None,
            'version': response[2] if len(response) > 2 else None,
            'features': response[3] if len(response) > 3 else None,
            'supported': len(response) >= 4
        }

        # Decode frequency from byte 4
        if len(response) >= 5:
            freq_map = {
                0x32: '433MHz',
                0x38: '470MHz',
                0x45: '868MHz',
                0x44: '915MHz',
                0x46: '170MHz'
            }
            version_info['frequency'] = freq_map.get(response[4], f'Unknown(0x{response[4]:02X})')
            version_info['freq_byte'] = response[4]
        else:
            version_info['frequency'] = 'Unknown'

        if self.debug:
            if version_info['supported']:
                print(f"Module Version: {version_info}")
            else:
                print(f"⚠ Version command partially supported or not available")
                print(f"  Raw response ({len(response)} bytes): {response.hex(' ').upper()}")

        return version_info

    def read_config(self) -> Dict[str, Any]:
        """
        Read current configuration from module.

        Returns:
            Configuration dictionary
        """
        command = bytes([self.CMDS['getConfig'], 0x00, 0x09])
        response = self._send_command(command, wait_time=0.2)
        return self.decode_config(response)

    def write_config(self, save: bool = True) -> bool:
        """
        Write current configuration to module.

        Args:
            save: If True, save to flash, otherwise temporary

        Returns:
            True if write successful, False otherwise
        """
        command = self.encode_config(save=save)
        response = self._send_command(command, wait_time=0.2)

        if len(response) < 3:
            return False

        # Check if response header matches expected
        expected_header = 0xC1
        if response[0] == expected_header:
            if self.debug:
                print("✓ Configuration written successfully")
            return True
        else:
            if self.debug:
                print(f"✗ Configuration write failed: {response.hex(' ').upper()}")
            return False

    def set_encryption_key(self, key_high: int, key_low: int) -> bool:
        """
        Set encryption key (16-bit).

        Args:
            key_high: High byte of encryption key (0x00-0xFF)
            key_low: Low byte of encryption key (0x00-0xFF)

        Returns:
            True if successful, False otherwise
        """
        # Update config
        self.config['crypt_h'] = key_high
        self.config['crypt_l'] = key_low

        # Write to module
        return self.write_config(save=True)

    def show_config(self) -> None:
        """Display current configuration in human-readable format."""
        print('=' * 60)
        print(f'E22 MODULE CONFIGURATION')
        print('=' * 60)
        print(f'Model:           {self.config["model"]}')
        print(f'Port:            {self.config["port"]}')
        print(f'Address:         0x{self.config["address"]:04X}')
        print(f'Network ID:      0x{self.config["netid"]:02X}')
        print(f'Channel:         {self.config["channel"]} (0x{self.config["channel"]:02X})')
        print('-' * 60)
        print(f'UART Baudrate:   {self.config["baudrate"]} bps')
        print(f'UART Parity:     {self.config["parity"]}')
        print(f'Air Data Rate:   {self.config["datarate"]} bps')
        print(f'Sub-Packet:      {self.config["subpckt"]}')
        print('-' * 60)
        power_str = self.power_map.get(self.config["txpower"], "Unknown")
        print(f'TX Power:        {power_str}')
        print(f'Ambient Noise:   {"Enabled" if self.config["amb_noise"] else "Disabled"}')
        print(f'RSSI Enable:     {"Enabled" if self.config["rssi"] else "Disabled"}')
        print('-' * 60)
        print(f'Trans Mode:      {self.TRANSMODE[self.config["transmode"]]}')
        print(f'Repeater:        {self.REPEATER[self.config["repeater"]]}')
        print(f'LBT:             {self.LBT[self.config["lbt"]]}')
        print(f'WOR Control:     {self.WORCTRL[self.config["worctrl"]]}')
        print(f'WOR Period:      {self.WUTIME[self.config["wutime"]]}')
        print('-' * 60)
        print(f'Encryption Key:  0x{self.config["crypt_h"]:02X}{self.config["crypt_l"]:02X}')
        print('=' * 60)


def main():
    """Example usage and testing."""
    import argparse

    parser = argparse.ArgumentParser(
        description='EBYTE E22 LoRa Module Configuration Tool (Improved)',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--port', default='/dev/ttyUSB0', help='Serial port')
    parser.add_argument('--model', default='900T22D', help='E22 model variant')
    parser.add_argument('--read', action='store_true', help='Read current config')
    parser.add_argument('--write', action='store_true', help='Write config to module')
    parser.add_argument('--version', action='store_true', help='Show module version info')
    parser.add_argument('--no-auto-detect', action='store_true', help='Disable auto-detection of module model')
    parser.add_argument('--address', type=lambda x: int(x, 0), help='Module address (hex)')
    parser.add_argument('--channel', type=int, help='Channel number')
    parser.add_argument('--power', choices=['22dBm', '17dBm', '13dBm', '10dBm'],
                       help='TX power')
    parser.add_argument('--air-rate', choices=['0.3k', '1.2k', '2.4k', '4.8k', '9.6k',
                                                '19.2k', '38.4k', '62.5k'],
                       help='Air data rate')
    parser.add_argument('--repeater', action='store_true', help='Enable repeater mode')
    parser.add_argument('--lbt', action='store_true', help='Enable LBT')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')

    args = parser.parse_args()

    # Create E22 instance
    e22 = EbyteE22(
        port=args.port,
        model=args.model,
        debug=args.debug
    )

    # Connect to module (with auto-detect unless disabled)
    if not e22.connect(auto_detect=not args.no_auto_detect):
        return 1

    try:
        if args.version:
            # Show version information
            version_info = e22.get_version()
            print('=' * 60)
            print('E22 MODULE VERSION INFO')
            print('=' * 60)

            if version_info.get('supported', False):
                print(f"Header:      0x{version_info['header']:02X}")
                print(f"Model:       0x{version_info['model']:02X}")
                print(f"Version:     0x{version_info['version']:02X}")
                print(f"Features:    0x{version_info['features']:02X}")
                print(f"Frequency:   {version_info.get('frequency', 'Unknown')}")
            else:
                print("⚠ Version command not fully supported by this module")
                print()
                print("Partial response received:")
                if version_info['header'] is not None:
                    print(f"  Header:    0x{version_info['header']:02X}")
                if version_info['model'] is not None:
                    print(f"  Model:     0x{version_info['model']:02X}")
                if version_info['version'] is not None:
                    print(f"  Version:   0x{version_info['version']:02X}")
                print()
                print("Recommendation: Use --model parameter to specify model manually")
                print("Example: --model 400T30S or --model 900T22D")

            print('=' * 60)

        if args.read:
            # Read configuration from module
            config = e22.read_config()
            e22.config.update(config)
            e22.show_config()

        if args.write:
            # Update config with command-line args
            if args.address is not None:
                e22.config['address'] = args.address
            if args.channel is not None:
                e22.config['channel'] = args.channel
            if args.power is not None:
                e22.config['txpower'] = e22.power_inv[args.power]
            if args.air_rate is not None:
                e22.config['datarate'] = args.air_rate
            if args.repeater:
                e22.config['repeater'] = 1
            if args.lbt:
                e22.config['lbt'] = 1

            # Write to module
            if e22.write_config():
                print("\n✓ Configuration written successfully")
                # Read back to verify
                config = e22.read_config()
                e22.config.update(config)
                e22.show_config()
            else:
                print("\n✗ Failed to write configuration")
                return 1

        if not args.read and not args.write:
            # Just show current local config
            e22.show_config()

    finally:
        e22.disconnect()

    return 0


if __name__ == '__main__':
    exit(main())
