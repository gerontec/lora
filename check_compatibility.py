#!/usr/bin/python3
"""
E22 LoRa Comprehensive Compatibility Checker

Checks all critical parameters between E22 and Dragino Gateway
"""
import serial
import time
import sys

def check_e22_config(port="/dev/ttyUSB0"):
    """Read and analyze E22 configuration for compatibility"""
    print("=" * 60)
    print("E22 LoRa Compatibility Checker")
    print("=" * 60)

    try:
        with serial.Serial(port, baudrate=9600, timeout=1) as ser:
            # Read product info
            ser.write(bytes([0xC1, 0x80, 0x07]))
            time.sleep(0.2)
            response = ser.read(100)
            if len(response) >= 10:
                product_info = response[3:10]
                print(f"\n✓ E22 Module detected: {product_info.hex(' ').upper()}")
            else:
                print(f"\n✗ Failed to read E22 product info")
                return False

            # Read configuration
            ser.write(bytes([0xC1, 0x00, 0x09]))
            time.sleep(0.2)
            response = ser.read(100)

            if len(response) < 12:
                print(f"✗ Failed to read E22 configuration")
                return False

            config = response[3:12]
            addh, addl, netid, reg0, reg1, reg2, reg3, reg4, reg5 = config

            print(f"\n{'Parameter':<25} {'Value':<20} {'Status'}")
            print("-" * 60)

            # Channel / Frequency
            channel = reg2
            freq = 850.125 + channel
            print(f"{'Channel':<25} {channel:<20} ", end="")
            if channel == 17:
                print("✓ Good (867.125 MHz matches Dragino)")
            elif channel == 18:
                print("⚠ OK (868.125 MHz, slight offset)")
            else:
                print(f"✗ BAD (use channel 17 or 18)")

            # Air Rate (critical!)
            air_rate_code = reg0 & 0x07
            air_rates = ["0.3k", "1.2k", "2.4k", "4.8k", "9.6k", "19.2k", "38.4k", "62.5k"]
            air_rate = air_rates[air_rate_code] if air_rate_code < len(air_rates) else "Unknown"
            print(f"{'Air Rate':<25} {air_rate:<20} ", end="")

            # Guess BW/SF from air rate
            if air_rate == "1.2k":
                print("✓ Good (likely 125kHz BW)")
            elif air_rate == "2.4k":
                print("⚠ Possible (might be 250kHz BW - BAD)")
            else:
                print("? Unknown compatibility")

            # Transmit Power
            power_code = reg1 & 0x03
            powers = ["13dBm", "18dBm", "22dBm", "27dBm", "30dBm"]
            power = powers[power_code] if power_code < len(powers) else "Unknown"
            print(f"{'Transmit Power':<25} {power:<20} ", end="")
            if power_code >= 1:
                print("✓ Good (sufficient power)")
            else:
                print("⚠ Low power (13dBm)")

            # Fixed Transmission Mode
            fixed_tx = "Fixed-point" if reg3 & 0x01 else "Transparent"
            print(f"{'Transmission Mode':<25} {fixed_tx:<20} ", end="")
            if fixed_tx == "Transparent":
                print("✓ Good (broadcast mode)")
            else:
                print("✗ BAD (needs addressing, use Transparent)")

            # LBT (Listen Before Talk)
            lbt = "Enabled" if reg3 & 0x10 else "Disabled"
            print(f"{'LBT (Listen Before Talk)':<25} {lbt:<20} ", end="")
            if lbt == "Disabled":
                print("✓ Good (no carrier sense delay)")
            else:
                print("⚠ Enabled (may delay transmission)")

            # Address
            address = (addh << 8) | addl
            print(f"{'Address':<25} 0x{address:04X:<17} ", end="")
            if fixed_tx == "Transparent":
                print("N/A (not used in Transparent mode)")
            else:
                print(f"Used in Fixed mode")

            print("\n" + "=" * 60)
            print("DRAGINO GATEWAY EXPECTATIONS:")
            print("-" * 60)
            print(f"{'Radio A Frequency':<25} 867.1 MHz")
            print(f"{'Radio B Frequency':<25} 868.5 MHz")
            print(f"{'Bandwidth':<25} 125 kHz")
            print(f"{'Spreading Factor':<25} SF7-SF12 (all)")
            print(f"{'Coding Rate':<25} 4/5 (typical)")
            print(f"{'Sync Word':<25} 0x34 (LoRaWAN public)")

            print("\n" + "=" * 60)
            print("RECOMMENDATIONS:")
            print("-" * 60)

            recommendations = []

            if channel not in [17, 18]:
                recommendations.append("✗ Change channel to 17: ./e22.py --channel 17")

            if air_rate != "1.2k":
                recommendations.append("✗ Change air rate to 1.2k: ./e22.py --air-rate 1.2k")

            if fixed_tx != "Transparent":
                recommendations.append("✗ Set transparent mode: ./e22.py --fixed-transmission 0")

            if power_code < 2:
                recommendations.append("⚠ Increase power to 22dBm: ./e22.py --power 22dBm")

            if lbt == "Enabled":
                recommendations.append("⚠ Disable LBT: ./e22.py --lbt-enable 0")

            if not recommendations:
                print("✓ Configuration looks good!")
                print("\nIf still no packets received, possible issues:")
                print("  1. E22 M0/M1 pins not in Normal Mode (M0=LOW, M1=LOW)")
                print("  2. Hardware issue (antenna, power, connections)")
                print("  3. Incompatible LoRa parameters (SF/BW/CR)")
                print("  4. Different Sync Word or Preamble length")
            else:
                for rec in recommendations:
                    print(rec)

                print("\nApply all recommendations:")
                cmd = "./e22.py"
                if channel not in [17, 18]:
                    cmd += " --channel 17"
                if air_rate != "1.2k":
                    cmd += " --air-rate 1.2k"
                if fixed_tx != "Transparent":
                    cmd += " --fixed-transmission 0"
                if power_code < 2:
                    cmd += " --power 22dBm"
                if lbt == "Enabled":
                    cmd += " --lbt-enable 0"

                print(f"\n{cmd}")

            return True

    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False

if __name__ == "__main__":
    port = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"
    check_e22_config(port)
