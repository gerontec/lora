#!/usr/bin/python3
import serial
import time
import argparse
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def send_command(ser, command):
    logging.debug(f"Sending command: {command.hex()}")
    ser.write(command)
    time.sleep(0.1)
    response = ser.read(100)
    logging.debug(f"Received response: {response.hex()}")
    return response

def read_config(ser):
    command = bytes([0xC1, 0x00, 0x09])
    response = send_command(ser, command)
    if len(response) < 12:
        raise ValueError(f"Unexpected response length or format: {response.hex()}")
    return response[3:12]  # Return 9 bytes of configuration data

def write_config(ser, config):
    command = bytes([0xC0, 0x00, 0x09] + config)
    response = send_command(ser, command)
    if response[0:3] != bytes([0xC1, 0x00, 0x09]):
        raise ValueError(f"Failed to write configuration: {response.hex()}")
    return response[3:12]

def write_encryption_keys(ser, key_high, key_low):
    command = bytes([0xC0, 0x00, 0x02, key_high, key_low])
    response = send_command(ser, command)
    if response[0:3] != bytes([0xC1, 0x00, 0x02]):
        raise ValueError(f"Failed to write encryption keys: {response.hex()}")

def read_product_info(ser):
    command = bytes([0xC1, 0x80, 0x07])
    response = send_command(ser, command)
    if len(response) < 10:
        raise ValueError(f"Unexpected response length or format for product info: {response.hex()}")
    return response[3:10]  # Return 7 bytes of product information

def parse_config(config):
    addh, addl, netid, reg0, reg1, reg2, reg3, reg4, reg5 = config
    address = (addh << 8) | addl
    network_address = netid
    channel = reg2
    air_rate_code = reg0 & 0x07
    air_rates = ["0.3k", "1.2k", "2.4k", "4.8k", "9.6k", "19.2k", "38.4k", "62.5k"]
    air_rate = air_rates[air_rate_code] if air_rate_code < len(air_rates) else "Unknown"
    baud_rate_code = (reg0 >> 5) & 0x03
    baud_rates = ["1200", "2400", "4800", "9600"]
    baud_rate = baud_rates[baud_rate_code] if baud_rate_code < len(baud_rates) else "Unknown"
    parity_code = (reg0 >> 3) & 0x03
    parities = ["8N1", "8O1", "8E1", "8N1"]
    parity = parities[parity_code]
    power_code = reg1 & 0x03
    powers = ["13dBm", "18dBm", "22dBm", "27dBm"]
    power = powers[power_code] if power_code < len(powers) else "Unknown"
    fixed_transmission = "Fixed-point" if reg3 & 0x01 else "Transparent"
    relay_function = "Enabled" if reg3 & 0x20 else "Disabled"
    lbt_enable = "Enabled" if reg3 & 0x10 else "Disabled"
    rssi_enable = "Enabled" if reg1 & 0x20 else "Disabled"
    
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
        "RSSI Enable": rssi_enable
    }

def create_config(address, network_address, channel, air_rate, baud_rate, parity, power, fixed_transmission, relay_function, lbt_enable, rssi_enable):
    addh = (address >> 8) & 0xFF
    addl = address & 0xFF
    netid = network_address

    air_rates = {"0.3k": 0, "1.2k": 1, "2.4k": 2, "4.8k": 3, "9.6k": 4, "19.2k": 5, "38.4k": 6, "62.5k": 7}
    baud_rates = {"1200": 0, "2400": 1, "4800": 2, "9600": 3}
    parities = {"8N1": 0, "8O1": 1, "8E1": 2}
    powers = {"13dBm": 0, "18dBm": 1, "22dBm": 2, "27dBm": 3}

    reg0 = (baud_rates[baud_rate] << 5) | (parities[parity] << 3) | air_rates[air_rate]
    reg1 = 0xE0 | powers[power]  # Base configuration for REG1

    # Modify REG1 for RSSI enable:
    if rssi_enable == "1":
        reg1 |= 0x20  # Enable RSSI by setting bit 5 in REG1
    else:
        reg1 &= ~0x20  # Disable RSSI by clearing bit 5 in REG1

    reg2 = channel
    reg3 = 0x80  # Base value for REG3
    if fixed_transmission == "1":
        reg3 |= 0x01
    if relay_function == "1":
        reg3 |= 0x20
    else:
        reg3 &= ~0x20  # Clear the relay function bit if it's disabled
    if lbt_enable == "1":
        reg3 |= 0x10
    reg4 = 0
    reg5 = 0

    return [addh, addl, netid, reg0, reg1, reg2, reg3, reg4, reg5]

def read_rssi(ser):
    command = bytes([0xC0, 0xC1, 0xC2, 0xC3, 0x00, 0x02])
    response = send_command(ser, command)
    
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
    # Check if response matches expected format
    if response[1] != 0x00 or response[2] != 0x02:
        raise ValueError(f"RSSI command response format incorrect: {response.hex()}")
    
    current_noise_rssi = response[3]
    last_received_rssi = response[4]
    
    current_noise_dbm = - (256 - current_noise_rssi)
    last_received_dbm = - (256 - last_received_rssi)
    
    return {
        "Current Noise RSSI": current_noise_dbm,
        "Last Received RSSI": last_received_dbm
    }
def main():
    parser = argparse.ArgumentParser(description="Read/Write configuration for E22 LoRa module")
    parser.add_argument("--port", default="/dev/ttyUSB0", help="Serial port")
    parser.add_argument("--address", type=lambda x: int(x, 0), help="Set address (e.g., 0x1234)")
    parser.add_argument("--network-address", type=lambda x: int(x, 0), default=0, help="Set network address (e.g., 0x00)")
    parser.add_argument("--channel", type=int, help="Set channel (0-83)")
    parser.add_argument("--air-rate", choices=["0.3k", "1.2k", "2.4k", "4.8k", "9.6k", "19.2k", "38.4k", "62.5k"], help="Set air rate")
    parser.add_argument("--baud-rate", choices=["1200", "2400", "4800", "9600"], help="Set baud rate")
    parser.add_argument("--parity", choices=["8N1", "8O1", "8E1"], help="Set parity")
    parser.add_argument("--power", choices=["13dBm", "18dBm", "22dBm", "27dBm"], help="Set transmitting power")
    parser.add_argument("--fixed-transmission", choices=["0", "1"], help="Set fixed-point transmission (0: Transparent, 1: Fixed-point)")
    parser.add_argument("--relay-function", choices=["0", "1"], help="Set relay function (0: Disable, 1: Enable)")
    parser.add_argument("--lbt-enable", choices=["0", "1"], help="Set LBT enable (0: Disable, 1: Enable)")
    parser.add_argument("--rssi-enable", choices=["0", "1"], help="Enable RSSI reading (0: Disable, 1: Enable)")
    parser.add_argument("--write-key", nargs=2, type=lambda x: int(x, 16), help="Write encryption key (high_byte low_byte in hex)")
    parser.add_argument("--read-product-info", action="store_true", help="Read product information")
    args = parser.parse_args()

    try:
        with serial.Serial(args.port, baudrate=9600, timeout=1) as ser:
            if args.write_key:
                write_encryption_keys(ser, *args.write_key)
                print(f"Encryption keys written: 0x{args.write_key[0]:02X} 0x{args.write_key[1]:02X}")

            if args.read_product_info or not any([args.address, args.network_address, args.channel, args.air_rate, args.baud_rate, args.parity, args.power, 
                                                  args.fixed_transmission, args.relay_function, args.lbt_enable, args.rssi_enable, args.write_key]):
                product_info = read_product_info(ser)
                print("Product Information:")
                print(f"Raw Product Info: {product_info.hex(' ').upper()}")

            current_config = read_config(ser)
            parsed_config = parse_config(current_config)

            if any([args.address, args.network_address, args.channel, args.air_rate, args.baud_rate, args.parity, args.power, 
                    args.fixed_transmission, args.relay_function, args.lbt_enable, args.rssi_enable]):
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

                new_config = create_config(
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

                write_config(ser, new_config)
                print("Configuration updated successfully.")
                current_config = read_config(ser)  # Re-read the config to verify changes
                parsed_config = parse_config(current_config)

            else:
                if not args.write_key:
                    print("No configuration arguments provided. Showing current configuration.")
            
            print("E22 Module Configuration:")
            for key, value in parsed_config.items():
                print(f"{key}: {value}")
            print(f"Raw Config: {current_config.hex(' ').upper()}")

            #if 'RSSI Enable' in parsed_config and parsed_config['RSSI Enable'] == "Enabled":
                #rssi_values = read_rssi(ser)
                #print(f"\nRSSI Values:")
                #print(f"Current Noise (dBm): {rssi_values['Current Noise RSSI']}")
                #print(f"Last Received (dBm): {rssi_values['Last Received RSSI']}")

            ## Print example command line
            print("\nExample Command Line for setting all possible arguments:")
            example_cmd = (
                "./e22.py --port /dev/ttyUSB0 "
                "--address 0x1234 --network-address 0x00 "
                "--channel 21 --air-rate 2.4k --baud-rate 9600 "
                "--parity 8N1 --power 22dBm "
                "--fixed-transmission 1 --relay-function 0 "
                "--lbt-enable 0 --rssi-enable 1 --write-key 07 08"
            )
            print(example_cmd)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
