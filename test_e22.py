#!/usr/bin/python3
"""
Comprehensive test suite for e22.py module.

Tests cover:
- Configuration parsing (binary to dict)
- Configuration creation (dict to binary)
- Round-trip conversion (create -> parse)
- RSSI conversion logic
- Edge cases and boundary conditions
- Bit-field manipulation
"""

import unittest
import sys
from unittest.mock import Mock, MagicMock, patch

# Mock the serial module before importing e22
sys.modules['serial'] = MagicMock()

import e22


class TestParseConfig(unittest.TestCase):
    """Test suite for the parse_config() function."""

    def test_parse_basic_config(self):
        """Test parsing a basic configuration."""
        # Config: Address=0x1234, NetAddr=0x00, Channel=21,
        # AirRate=2.4k(2), BaudRate=9600(3), Parity=8N1(0), Power=22dBm(2)
        config = [0x12, 0x34, 0x00, 0x62, 0xE2, 0x15, 0x80, 0x00, 0x00]
        result = e22.parse_config(config)

        self.assertEqual(result["Address"], "0x1234")
        self.assertEqual(result["Network Address"], "0x00")
        self.assertEqual(result["Channel"], 21)
        self.assertEqual(result["Air Rate"], "2.4k")
        self.assertEqual(result["Baud Rate"], "9600")
        self.assertEqual(result["Parity"], "8N1")
        self.assertEqual(result["Transmitting Power"], "22dBm")

    def test_parse_all_air_rates(self):
        """Test parsing all possible air rate values."""
        air_rates = ["0.3k", "1.2k", "2.4k", "4.8k", "9.6k", "19.2k", "38.4k", "62.5k"]

        for i, expected_rate in enumerate(air_rates):
            config = [0x00, 0x00, 0x00, i, 0xE0, 0x00, 0x80, 0x00, 0x00]
            result = e22.parse_config(config)
            self.assertEqual(result["Air Rate"], expected_rate,
                           f"Failed for air rate code {i}")

    def test_parse_all_baud_rates(self):
        """Test parsing all possible baud rate values."""
        baud_rates = ["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"]

        for i, expected_baud in enumerate(baud_rates):
            config = [0x00, 0x00, 0x00, i << 5, 0xE0, 0x00, 0x80, 0x00, 0x00]
            result = e22.parse_config(config)
            self.assertEqual(result["Baud Rate"], expected_baud,
                           f"Failed for baud rate code {i}")

    def test_parse_all_parity_modes(self):
        """Test parsing all possible parity modes."""
        parities = ["8N1", "8O1", "8E1", "8N1"]  # Note: code 3 also maps to 8N1

        for i, expected_parity in enumerate(parities):
            config = [0x00, 0x00, 0x00, i << 3, 0xE0, 0x00, 0x80, 0x00, 0x00]
            result = e22.parse_config(config)
            self.assertEqual(result["Parity"], expected_parity,
                           f"Failed for parity code {i}")

    def test_parse_all_power_levels(self):
        """Test parsing all possible transmitting power levels."""
        powers = ["13dBm", "18dBm", "22dBm", "27dBm"]

        for i, expected_power in enumerate(powers):
            config = [0x00, 0x00, 0x00, 0x00, 0xE0 | i, 0x00, 0x80, 0x00, 0x00]
            result = e22.parse_config(config)
            self.assertEqual(result["Transmitting Power"], expected_power,
                           f"Failed for power code {i}")

    def test_parse_fixed_transmission_enabled(self):
        """Test parsing with fixed-point transmission enabled."""
        config = [0x00, 0x00, 0x00, 0x00, 0xE0, 0x00, 0xC0, 0x00, 0x00]  # REG3 bit 6 set
        result = e22.parse_config(config)
        self.assertEqual(result["Fixed Transmission"], "Fixed-point")

    def test_parse_fixed_transmission_disabled(self):
        """Test parsing with transparent transmission mode."""
        config = [0x00, 0x00, 0x00, 0x00, 0xE0, 0x00, 0x80, 0x00, 0x00]  # REG3 bit 6 clear
        result = e22.parse_config(config)
        self.assertEqual(result["Fixed Transmission"], "Transparent")

    def test_parse_relay_function_enabled(self):
        """Test parsing with relay function enabled."""
        config = [0x00, 0x00, 0x00, 0x00, 0xE0, 0x00, 0xA0, 0x00, 0x00]  # REG3 bit 5 set
        result = e22.parse_config(config)
        self.assertEqual(result["Relay Function"], "Enabled")

    def test_parse_relay_function_disabled(self):
        """Test parsing with relay function disabled."""
        config = [0x00, 0x00, 0x00, 0x00, 0xE0, 0x00, 0x80, 0x00, 0x00]  # REG3 bit 5 clear
        result = e22.parse_config(config)
        self.assertEqual(result["Relay Function"], "Disabled")

    def test_parse_lbt_enabled(self):
        """Test parsing with LBT (Listen Before Talk) enabled."""
        config = [0x00, 0x00, 0x00, 0x00, 0xE0, 0x00, 0x90, 0x00, 0x00]  # REG3 bit 4 set
        result = e22.parse_config(config)
        self.assertEqual(result["LBT Enable"], "Enabled")

    def test_parse_lbt_disabled(self):
        """Test parsing with LBT disabled."""
        config = [0x00, 0x00, 0x00, 0x00, 0xE0, 0x00, 0x80, 0x00, 0x00]  # REG3 bit 4 clear
        result = e22.parse_config(config)
        self.assertEqual(result["LBT Enable"], "Disabled")

    def test_parse_rssi_enabled(self):
        """Test parsing with RSSI enabled."""
        config = [0x00, 0x00, 0x00, 0x00, 0xE0 | 0x20, 0x00, 0x80, 0x00, 0x00]  # REG1 bit 5 set
        result = e22.parse_config(config)
        self.assertEqual(result["RSSI Enable"], "Enabled")

    def test_parse_rssi_disabled(self):
        """Test parsing with RSSI disabled."""
        config = [0x00, 0x00, 0x00, 0x00, 0xC0, 0x00, 0x80, 0x00, 0x00]  # REG1 bit 5 clear (0xC0 = 0b11000000)
        result = e22.parse_config(config)
        self.assertEqual(result["RSSI Enable"], "Disabled")

    def test_parse_noise_enabled(self):
        """Test parsing with noise measurement enabled."""
        config = [0x00, 0x00, 0x00, 0x00, 0xE0, 0x00, 0x80, 0x00, 0x00]  # REG3 bit 7 set (0x80)
        result = e22.parse_config(config)
        self.assertEqual(result["Noise Enable"], "Enabled")

    def test_parse_noise_disabled(self):
        """Test parsing with noise measurement disabled."""
        config = [0x00, 0x00, 0x00, 0x00, 0xE0, 0x00, 0x00, 0x00, 0x00]  # REG3 bit 7 clear
        result = e22.parse_config(config)
        self.assertEqual(result["Noise Enable"], "Disabled")

    def test_parse_max_address(self):
        """Test parsing maximum address value."""
        config = [0xFF, 0xFF, 0xFF, 0x00, 0xE0, 0x00, 0x80, 0x00, 0x00]
        result = e22.parse_config(config)
        self.assertEqual(result["Address"], "0xFFFF")
        self.assertEqual(result["Network Address"], "0xFF")

    def test_parse_all_channels(self):
        """Test parsing various channel values."""
        for channel in [0, 21, 42, 83]:
            config = [0x00, 0x00, 0x00, 0x00, 0xE0, channel, 0x80, 0x00, 0x00]
            result = e22.parse_config(config)
            self.assertEqual(result["Channel"], channel)

    def test_parse_complex_configuration(self):
        """Test parsing a complex real-world configuration."""
        # Address=0xABCD, NetAddr=0x12, Channel=50, AirRate=19.2k,
        # BaudRate=115200, Parity=8E1, Power=27dBm, All features enabled
        config = [0xAB, 0xCD, 0x12, 0xF5, 0xE3, 0x32, 0xF0, 0x00, 0x00]
        result = e22.parse_config(config)

        self.assertEqual(result["Address"], "0xABCD")
        self.assertEqual(result["Network Address"], "0x12")
        self.assertEqual(result["Channel"], 50)
        self.assertEqual(result["Air Rate"], "19.2k")
        self.assertEqual(result["Baud Rate"], "115200")
        self.assertEqual(result["Parity"], "8E1")
        self.assertEqual(result["Transmitting Power"], "27dBm")


class TestCreateConfig(unittest.TestCase):
    """Test suite for the create_config() function."""

    def test_create_basic_config(self):
        """Test creating a basic configuration."""
        config = e22.create_config(
            address=0x1234,
            network_address=0x00,
            channel=21,
            air_rate="2.4k",
            baud_rate="9600",
            parity="8N1",
            power="22dBm",
            fixed_transmission="0",
            relay_function="0",
            lbt_enable="0",
            rssi_enable="0",
            noise_enable="0"
        )

        self.assertEqual(config[0], 0x12)  # ADDH
        self.assertEqual(config[1], 0x34)  # ADDL
        self.assertEqual(config[2], 0x00)  # NETID
        self.assertEqual(config[4] & 0x03, 2)  # Power code in REG1
        self.assertEqual(config[5], 21)  # Channel in REG2

    def test_create_all_air_rates(self):
        """Test creating configs with all air rate options."""
        air_rates = ["0.3k", "1.2k", "2.4k", "4.8k", "9.6k", "19.2k", "38.4k", "62.5k"]

        for i, air_rate in enumerate(air_rates):
            config = e22.create_config(
                address=0, network_address=0, channel=0,
                air_rate=air_rate, baud_rate="9600", parity="8N1",
                power="13dBm", fixed_transmission="0", relay_function="0",
                lbt_enable="0", rssi_enable="0", noise_enable="0"
            )
            self.assertEqual(config[3] & 0x07, i, f"Failed for {air_rate}")

    def test_create_all_baud_rates(self):
        """Test creating configs with all baud rate options."""
        baud_rates = ["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"]

        for i, baud_rate in enumerate(baud_rates):
            config = e22.create_config(
                address=0, network_address=0, channel=0,
                air_rate="2.4k", baud_rate=baud_rate, parity="8N1",
                power="13dBm", fixed_transmission="0", relay_function="0",
                lbt_enable="0", rssi_enable="0", noise_enable="0"
            )
            self.assertEqual((config[3] >> 5) & 0x07, i, f"Failed for {baud_rate}")

    def test_create_all_parities(self):
        """Test creating configs with all parity options."""
        parities = {"8N1": 0, "8O1": 1, "8E1": 2}

        for parity, expected_code in parities.items():
            config = e22.create_config(
                address=0, network_address=0, channel=0,
                air_rate="2.4k", baud_rate="9600", parity=parity,
                power="13dBm", fixed_transmission="0", relay_function="0",
                lbt_enable="0", rssi_enable="0", noise_enable="0"
            )
            self.assertEqual((config[3] >> 3) & 0x03, expected_code, f"Failed for {parity}")

    def test_create_all_power_levels(self):
        """Test creating configs with all power levels."""
        powers = {"13dBm": 0, "18dBm": 1, "22dBm": 2, "27dBm": 3}

        for power, expected_code in powers.items():
            config = e22.create_config(
                address=0, network_address=0, channel=0,
                air_rate="2.4k", baud_rate="9600", parity="8N1",
                power=power, fixed_transmission="0", relay_function="0",
                lbt_enable="0", rssi_enable="0", noise_enable="0"
            )
            self.assertEqual(config[4] & 0x03, expected_code, f"Failed for {power}")

    def test_create_fixed_transmission_enabled(self):
        """Test creating config with fixed transmission enabled."""
        config = e22.create_config(
            address=0, network_address=0, channel=0,
            air_rate="2.4k", baud_rate="9600", parity="8N1",
            power="13dBm", fixed_transmission="1", relay_function="0",
            lbt_enable="0", rssi_enable="0", noise_enable="0"
        )
        self.assertTrue(config[6] & 0x40, "Fixed transmission bit should be set")

    def test_create_fixed_transmission_disabled(self):
        """Test creating config with transparent mode."""
        config = e22.create_config(
            address=0, network_address=0, channel=0,
            air_rate="2.4k", baud_rate="9600", parity="8N1",
            power="13dBm", fixed_transmission="0", relay_function="0",
            lbt_enable="0", rssi_enable="0", noise_enable="0"
        )
        self.assertFalse(config[6] & 0x40, "Fixed transmission bit should be clear")

    def test_create_relay_function_enabled(self):
        """Test creating config with relay function enabled."""
        config = e22.create_config(
            address=0, network_address=0, channel=0,
            air_rate="2.4k", baud_rate="9600", parity="8N1",
            power="13dBm", fixed_transmission="0", relay_function="1",
            lbt_enable="0", rssi_enable="0", noise_enable="0"
        )
        self.assertTrue(config[6] & 0x20, "Relay function bit should be set")

    def test_create_relay_function_disabled(self):
        """Test creating config with relay function disabled."""
        config = e22.create_config(
            address=0, network_address=0, channel=0,
            air_rate="2.4k", baud_rate="9600", parity="8N1",
            power="13dBm", fixed_transmission="0", relay_function="0",
            lbt_enable="0", rssi_enable="0", noise_enable="0"
        )
        self.assertFalse(config[6] & 0x20, "Relay function bit should be clear")

    def test_create_lbt_enabled(self):
        """Test creating config with LBT enabled."""
        config = e22.create_config(
            address=0, network_address=0, channel=0,
            air_rate="2.4k", baud_rate="9600", parity="8N1",
            power="13dBm", fixed_transmission="0", relay_function="0",
            lbt_enable="1", rssi_enable="0", noise_enable="0"
        )
        self.assertTrue(config[6] & 0x10, "LBT bit should be set")

    def test_create_lbt_disabled(self):
        """Test creating config with LBT disabled."""
        config = e22.create_config(
            address=0, network_address=0, channel=0,
            air_rate="2.4k", baud_rate="9600", parity="8N1",
            power="13dBm", fixed_transmission="0", relay_function="0",
            lbt_enable="0", rssi_enable="0", noise_enable="0"
        )
        self.assertFalse(config[6] & 0x10, "LBT bit should be clear")

    def test_create_rssi_enabled(self):
        """Test creating config with RSSI enabled."""
        config = e22.create_config(
            address=0, network_address=0, channel=0,
            air_rate="2.4k", baud_rate="9600", parity="8N1",
            power="13dBm", fixed_transmission="0", relay_function="0",
            lbt_enable="0", rssi_enable="1", noise_enable="0"
        )
        self.assertTrue(config[4] & 0x20, "RSSI bit should be set in REG1")

    def test_create_rssi_disabled(self):
        """Test creating config with RSSI disabled."""
        config = e22.create_config(
            address=0, network_address=0, channel=0,
            air_rate="2.4k", baud_rate="9600", parity="8N1",
            power="13dBm", fixed_transmission="0", relay_function="0",
            lbt_enable="0", rssi_enable="0", noise_enable="0"
        )
        self.assertFalse(config[4] & 0x20, "RSSI bit should be clear in REG1")

    def test_create_noise_enabled(self):
        """Test creating config with noise measurement enabled."""
        config = e22.create_config(
            address=0, network_address=0, channel=0,
            air_rate="2.4k", baud_rate="9600", parity="8N1",
            power="13dBm", fixed_transmission="0", relay_function="0",
            lbt_enable="0", rssi_enable="0", noise_enable="1"
        )
        self.assertTrue(config[6] & 0x80, "Noise bit should be set in REG3")

    def test_create_noise_disabled(self):
        """Test creating config with noise measurement disabled."""
        config = e22.create_config(
            address=0, network_address=0, channel=0,
            air_rate="2.4k", baud_rate="9600", parity="8N1",
            power="13dBm", fixed_transmission="0", relay_function="0",
            lbt_enable="0", rssi_enable="0", noise_enable="0"
        )
        self.assertFalse(config[6] & 0x80, "Noise bit should be clear in REG3")

    def test_create_address_boundaries(self):
        """Test creating configs with boundary address values."""
        # Minimum address
        config = e22.create_config(
            address=0x0000, network_address=0x00, channel=0,
            air_rate="2.4k", baud_rate="9600", parity="8N1",
            power="13dBm", fixed_transmission="0", relay_function="0",
            lbt_enable="0", rssi_enable="0"
        )
        self.assertEqual(config[0], 0x00)
        self.assertEqual(config[1], 0x00)

        # Maximum address
        config = e22.create_config(
            address=0xFFFF, network_address=0xFF, channel=0,
            air_rate="2.4k", baud_rate="9600", parity="8N1",
            power="13dBm", fixed_transmission="0", relay_function="0",
            lbt_enable="0", rssi_enable="0"
        )
        self.assertEqual(config[0], 0xFF)
        self.assertEqual(config[1], 0xFF)
        self.assertEqual(config[2], 0xFF)

    def test_create_all_features_enabled(self):
        """Test creating config with all features enabled."""
        config = e22.create_config(
            address=0xABCD, network_address=0x12, channel=50,
            air_rate="19.2k", baud_rate="115200", parity="8E1",
            power="27dBm", fixed_transmission="1", relay_function="1",
            lbt_enable="1", rssi_enable="1", noise_enable="1"
        )

        # Verify all bits are set correctly
        self.assertEqual(config[0], 0xAB)
        self.assertEqual(config[1], 0xCD)
        self.assertEqual(config[2], 0x12)
        self.assertTrue(config[6] & 0x80)  # Noise
        self.assertTrue(config[6] & 0x40)  # Fixed transmission
        self.assertTrue(config[6] & 0x20)  # Relay
        self.assertTrue(config[6] & 0x10)  # LBT
        self.assertTrue(config[4] & 0x20)  # RSSI


class TestRoundTripConversion(unittest.TestCase):
    """Test round-trip conversion: create_config -> parse_config."""

    def test_roundtrip_basic(self):
        """Test basic round-trip conversion."""
        original_params = {
            "address": 0x1234,
            "network_address": 0x00,
            "channel": 21,
            "air_rate": "2.4k",
            "baud_rate": "9600",
            "parity": "8N1",
            "power": "22dBm",
            "fixed_transmission": "0",
            "relay_function": "0",
            "lbt_enable": "0",
            "rssi_enable": "0",
            "noise_enable": "0"
        }

        config = e22.create_config(**original_params)
        parsed = e22.parse_config(config)

        self.assertEqual(parsed["Address"], f"0x{original_params['address']:04X}")
        self.assertEqual(parsed["Network Address"], f"0x{original_params['network_address']:02X}")
        self.assertEqual(parsed["Channel"], original_params["channel"])
        self.assertEqual(parsed["Air Rate"], original_params["air_rate"])
        self.assertEqual(parsed["Baud Rate"], original_params["baud_rate"])
        self.assertEqual(parsed["Parity"], original_params["parity"])
        self.assertEqual(parsed["Transmitting Power"], original_params["power"])
        self.assertEqual(parsed["Fixed Transmission"], "Transparent")
        self.assertEqual(parsed["Relay Function"], "Disabled")
        self.assertEqual(parsed["LBT Enable"], "Disabled")
        self.assertEqual(parsed["RSSI Enable"], "Disabled")
        self.assertEqual(parsed["Noise Enable"], "Disabled")

    def test_roundtrip_all_features_enabled(self):
        """Test round-trip with all features enabled."""
        original_params = {
            "address": 0xABCD,
            "network_address": 0x12,
            "channel": 50,
            "air_rate": "19.2k",
            "baud_rate": "115200",
            "parity": "8E1",
            "power": "27dBm",
            "fixed_transmission": "1",
            "relay_function": "1",
            "lbt_enable": "1",
            "rssi_enable": "1",
            "noise_enable": "1"
        }

        config = e22.create_config(**original_params)
        parsed = e22.parse_config(config)

        self.assertEqual(parsed["Address"], "0xABCD")
        self.assertEqual(parsed["Network Address"], "0x12")
        self.assertEqual(parsed["Channel"], 50)
        self.assertEqual(parsed["Air Rate"], "19.2k")
        self.assertEqual(parsed["Baud Rate"], "115200")
        self.assertEqual(parsed["Parity"], "8E1")
        self.assertEqual(parsed["Transmitting Power"], "27dBm")
        self.assertEqual(parsed["Fixed Transmission"], "Fixed-point")
        self.assertEqual(parsed["Relay Function"], "Enabled")
        self.assertEqual(parsed["LBT Enable"], "Enabled")
        self.assertEqual(parsed["RSSI Enable"], "Enabled")
        self.assertEqual(parsed["Noise Enable"], "Enabled")

    def test_roundtrip_various_combinations(self):
        """Test round-trip with various parameter combinations."""
        test_cases = [
            # Test each air rate
            ("0.3k", "1200", "8N1", "13dBm"),
            ("1.2k", "2400", "8O1", "18dBm"),
            ("4.8k", "4800", "8E1", "22dBm"),
            ("9.6k", "19200", "8N1", "27dBm"),
            ("38.4k", "38400", "8N1", "13dBm"),
            ("62.5k", "115200", "8N1", "27dBm"),
        ]

        for air_rate, baud_rate, parity, power in test_cases:
            with self.subTest(air_rate=air_rate, baud_rate=baud_rate):
                config = e22.create_config(
                    address=0x0001, network_address=0x00, channel=10,
                    air_rate=air_rate, baud_rate=baud_rate, parity=parity,
                    power=power, fixed_transmission="0", relay_function="0",
                    lbt_enable="0", rssi_enable="0", noise_enable="0"
                )
                parsed = e22.parse_config(config)

                self.assertEqual(parsed["Air Rate"], air_rate)
                self.assertEqual(parsed["Baud Rate"], baud_rate)
                self.assertEqual(parsed["Parity"], parity)
                self.assertEqual(parsed["Transmitting Power"], power)


class TestReadRSSI(unittest.TestCase):
    """Test suite for the read_rssi() function."""

    @patch('e22.send_command')
    def test_rssi_conversion_zero(self, mock_send):
        """Test RSSI conversion with zero values."""
        # Mock response: header (3 bytes) + noise=0 + last_rssi=0
        mock_send.return_value = bytes([0xC1, 0x00, 0x02, 0x00, 0x00])

        ser_mock = Mock()
        result = e22.read_rssi(ser_mock)

        # RSSI calculation: -(256 - 0) = -256 dBm
        self.assertEqual(result["Current Noise RSSI"], -256)
        self.assertEqual(result["Last Received RSSI"], -256)

    @patch('e22.send_command')
    def test_rssi_conversion_typical(self, mock_send):
        """Test RSSI conversion with typical values."""
        # Mock response: noise=200 (-56dBm), last_rssi=180 (-76dBm)
        mock_send.return_value = bytes([0xC1, 0x00, 0x02, 200, 180])

        ser_mock = Mock()
        result = e22.read_rssi(ser_mock)

        # RSSI calculation: -(256 - value)
        self.assertEqual(result["Current Noise RSSI"], -56)
        self.assertEqual(result["Last Received RSSI"], -76)

    @patch('e22.send_command')
    def test_rssi_conversion_strong_signal(self, mock_send):
        """Test RSSI conversion with strong signal."""
        # Mock response: noise=240 (-16dBm), last_rssi=230 (-26dBm)
        mock_send.return_value = bytes([0xC1, 0x00, 0x02, 240, 230])

        ser_mock = Mock()
        result = e22.read_rssi(ser_mock)

        self.assertEqual(result["Current Noise RSSI"], -16)
        self.assertEqual(result["Last Received RSSI"], -26)

    @patch('e22.send_command')
    def test_rssi_conversion_weak_signal(self, mock_send):
        """Test RSSI conversion with weak signal."""
        # Mock response: noise=100 (-156dBm), last_rssi=80 (-176dBm)
        mock_send.return_value = bytes([0xC1, 0x00, 0x02, 100, 80])

        ser_mock = Mock()
        result = e22.read_rssi(ser_mock)

        self.assertEqual(result["Current Noise RSSI"], -156)
        self.assertEqual(result["Last Received RSSI"], -176)

    @patch('e22.send_command')
    def test_rssi_conversion_max_value(self, mock_send):
        """Test RSSI conversion with maximum value."""
        # Mock response: noise=255 (-1dBm), last_rssi=255 (-1dBm)
        mock_send.return_value = bytes([0xC1, 0x00, 0x02, 255, 255])

        ser_mock = Mock()
        result = e22.read_rssi(ser_mock)

        self.assertEqual(result["Current Noise RSSI"], -1)
        self.assertEqual(result["Last Received RSSI"], -1)

    @patch('e22.send_command')
    def test_rssi_invalid_response_length(self, mock_send):
        """Test RSSI with invalid response length."""
        # Mock response with wrong length
        mock_send.return_value = bytes([0xC1, 0x00, 0x02])

        ser_mock = Mock()
        with self.assertRaises(ValueError) as context:
            e22.read_rssi(ser_mock)

        self.assertIn("Unexpected RSSI response format", str(context.exception))

    @patch('e22.send_command')
    def test_rssi_invalid_response_header(self, mock_send):
        """Test RSSI with invalid response header."""
        # Mock response with wrong header
        mock_send.return_value = bytes([0xFF, 0xFF, 0xFF, 200, 180])

        ser_mock = Mock()
        with self.assertRaises(ValueError) as context:
            e22.read_rssi(ser_mock)

        self.assertIn("Unexpected RSSI response format", str(context.exception))


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""

    def test_parse_config_invalid_length(self):
        """Test parsing with invalid config length."""
        # parse_config expects exactly 9 bytes
        short_config = [0x00, 0x00, 0x00]

        # This should raise an error during unpacking
        with self.assertRaises(ValueError):
            e22.parse_config(short_config)

    def test_parse_config_air_rate_masking(self):
        """Test that air rate code masking works correctly."""
        # Air rate uses only 3 bits (mask 0x07), so 0x08 becomes 0x00 after masking
        config = [0x00, 0x00, 0x00, 0x08, 0xE0, 0x00, 0x80, 0x00, 0x00]
        result = e22.parse_config(config)
        # 0x08 & 0x07 = 0x00, which maps to "0.3k"
        self.assertEqual(result["Air Rate"], "0.3k")

    def test_parse_config_unknown_baud_rate(self):
        """Test parsing with out-of-range baud rate code."""
        # Baud rate code 8 is out of range (valid: 0-7)
        # Note: This can't happen with 3 bits, but test the bounds check
        config = [0x00, 0x00, 0x00, 0xFF, 0xE0, 0x00, 0x80, 0x00, 0x00]
        result = e22.parse_config(config)
        # Should handle gracefully
        self.assertIsNotNone(result["Baud Rate"])

    def test_create_config_channel_boundaries(self):
        """Test creating config with channel boundary values."""
        # Valid channels: 0-83
        for channel in [0, 1, 41, 82, 83]:
            config = e22.create_config(
                address=0, network_address=0, channel=channel,
                air_rate="2.4k", baud_rate="9600", parity="8N1",
                power="13dBm", fixed_transmission="0", relay_function="0",
                lbt_enable="0", rssi_enable="0"
            )
            self.assertEqual(config[5], channel)

    def test_create_config_default_noise_enable(self):
        """Test that noise_enable defaults to '0' when not provided."""
        config = e22.create_config(
            address=0, network_address=0, channel=0,
            air_rate="2.4k", baud_rate="9600", parity="8N1",
            power="13dBm", fixed_transmission="0", relay_function="0",
            lbt_enable="0", rssi_enable="0"
            # noise_enable not provided, should default to "0"
        )
        # With noise_enable="0", bit 7 should be clear
        # But base value is 0x80, so we need to check the logic
        # Actually, looking at the code, if noise_enable="0", it clears bit 7
        # So the result should have bit 7 clear
        self.assertFalse(config[6] & 0x80, "Noise bit should be clear by default")


class TestBitFieldManipulation(unittest.TestCase):
    """Test bit-field manipulation correctness."""

    def test_reg0_bit_fields(self):
        """Test REG0 bit field packing and unpacking."""
        # REG0 format: [7:5]=baud, [4:3]=parity, [2:0]=air_rate
        config = e22.create_config(
            address=0, network_address=0, channel=0,
            air_rate="4.8k",      # code 3 -> bits [2:0] = 011
            baud_rate="57600",    # code 6 -> bits [7:5] = 110
            parity="8E1",         # code 2 -> bits [4:3] = 10
            power="13dBm", fixed_transmission="0", relay_function="0",
            lbt_enable="0", rssi_enable="0"
        )

        reg0 = config[3]
        # Expected: 0b11010011 = 0xD3
        self.assertEqual(reg0 & 0x07, 3, "Air rate bits incorrect")
        self.assertEqual((reg0 >> 3) & 0x03, 2, "Parity bits incorrect")
        self.assertEqual((reg0 >> 5) & 0x07, 6, "Baud rate bits incorrect")

    def test_reg1_bit_fields(self):
        """Test REG1 bit field packing."""
        # REG1 format: base=0xE0, bit 5=RSSI, bits [1:0]=power
        config = e22.create_config(
            address=0, network_address=0, channel=0,
            air_rate="2.4k", baud_rate="9600", parity="8N1",
            power="27dBm",        # code 3
            fixed_transmission="0", relay_function="0",
            lbt_enable="0", rssi_enable="1"  # Enable RSSI
        )

        reg1 = config[4]
        # Expected: 0xE0 | 0x20 | 0x03 = 0xE3
        self.assertEqual(reg1 & 0x03, 3, "Power bits incorrect")
        self.assertTrue(reg1 & 0x20, "RSSI bit should be set")
        self.assertTrue(reg1 & 0xE0, "Base bits should be set")

    def test_reg3_bit_fields(self):
        """Test REG3 bit field packing."""
        # REG3 format: bit 7=noise, bit 6=fixed, bit 5=relay, bit 4=lbt
        config = e22.create_config(
            address=0, network_address=0, channel=0,
            air_rate="2.4k", baud_rate="9600", parity="8N1",
            power="13dBm",
            fixed_transmission="1",   # bit 6
            relay_function="1",       # bit 5
            lbt_enable="1",           # bit 4
            rssi_enable="0",
            noise_enable="1"          # bit 7
        )

        reg3 = config[6]
        # Expected: 0x80 | 0x40 | 0x20 | 0x10 = 0xF0
        self.assertTrue(reg3 & 0x80, "Noise bit should be set")
        self.assertTrue(reg3 & 0x40, "Fixed transmission bit should be set")
        self.assertTrue(reg3 & 0x20, "Relay bit should be set")
        self.assertTrue(reg3 & 0x10, "LBT bit should be set")
        self.assertEqual(reg3, 0xF0, "REG3 should be 0xF0")


def run_tests():
    """Run all tests and print results."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestParseConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestCreateConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestRoundTripConversion))
    suite.addTests(loader.loadTestsFromTestCase(TestReadRSSI))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestBitFieldManipulation))

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
