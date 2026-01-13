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
        "LBT Enable": lbt_enable
    }

def create_config(address, network_address, channel, air_rate, baud_rate, parity, power, fixed_transmission, relay_function, lbt_enable):
    addh = (address >> 8) & 0xFF
    addl = address & 0xFF
    netid = network_address

    air_rates = {"0.3k": 0, "1.2k": 1, "2.4k": 2, "4.8k": 3, "9.6k": 4, "19.2k": 5, "38.4k": 6, "62.5k": 7}
    baud_rates = {"1200": 0, "2400": 1, "4800": 2, "9600": 3}
    parities = {"8N1": 0, "8O1": 1, "8E1": 2}
    # REG1 lower two bits encode 13/18/22/27 dBm (values 0-3). 30 dBm is not
    # representable in these two bits for standard E22 modules. If the user
    # requests 30dBm explicitly, fail with a clear message rather than writing
    # an incorrect value.
    powers = {"13dBm": 0, "18dBm": 1, "22dBm": 2, "27dBm": 3}

    if power == "30dBm":
        raise ValueError("30dBm is not supported via REG1 on standard E22 modules. Use an E90 module or hardware PWMAX control for 30dBm.")

    reg0 = (baud_rates[baud_rate] << 5) | (parities[parity] << 3) | air_rates[air_rate]
    reg1 = 0xE0 | powers[power]  # Assuming other bits in REG1 are set to 1
    reg2 = channel
    reg3 = 0x80  # Base value, not 0xA0
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

def main():
    parser = argparse.ArgumentParser(description="Read/Write configuration for E22 LoRa module")
    parser.add_argument("--port", default="/dev/ttyUSB0", help="Serial port")
    parser.add_argument("--address", type=lambda x: int(x, 0), help="Set address (e.g., 0x1234)")
    parser.add_argument("--network-address", type=lambda x: int(x, 0), default=0, help="Set network address (e.g., 0x00)")
    parser.add_argument("--channel", type=int, help="Set channel (0-83)")
    parser.add_argument("--air-rate", choices=["0.3k", "1.2k", "2.4k", "4.8k", "9.6k", "19.2k", "38.4k", "62.5k"], help="Set air rate")
    parser.add_argument("--baud-rate", choices=["1200", "2400", "4800", "9600"], help="Set baud rate")
    parser.add_argument("--parity", choices=["8N1", "8O1", "8E1"], help="Set parity")
    # E22 supports 13/18/22/27 dBm via REG1. 30 dBm (1W) is not representable
    # by REG1 for standard E22 modules; it requires different hardware or a
    # different module (e.g. E90). We allow the CLI value for visibility but
    # will raise an error if the user attempts to write 30dBm.
    parser.add_argument("--power", choices=["13dBm", "18dBm", "22dBm", "27dBm", "30dBm"], help="Set transmitting power (13/18/22/27 dBm; 30 dBm may not be supported)")
    parser.add_argument("--fixed-transmission", choices=["0", "1"], help="Set fixed-point transmission (0: Transparent, 1: Fixed-point)")
    parser.add_argument("--relay-function", choices=["0", "1"], help="Set relay function (0: Disable, 1: Enable)")
    parser.add_argument("--lbt-enable", choices=["0", "1"], help="Set LBT enable (0: Disable, 1: Enable)")
    args = parser.parse_args()

    try:
        with serial.Serial(args.port, baudrate=9600, timeout=1) as ser:
            # Read current configuration
            current_config = read_config(ser)
            parsed_config = parse_config(current_config)

            # Check if any configuration arguments are provided
            if any([args.address, args.network_address, args.channel, args.air_rate, args.baud_rate, args.parity, args.power, 
                    args.fixed_transmission, args.relay_function, args.lbt_enable]):
                # Update configuration with provided arguments
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

                # Create new configuration
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
                    "1" if parsed_config['LBT Enable'] == "Enabled" else "0"
                )

                # Write new configuration
                write_config(ser, new_config)
                print("Configuration updated successfully.")
                
                # Read the configuration again to confirm changes
                config_data = read_config(ser)
            else:
                print("No arguments provided. Showing current configuration.")
                config_data = current_config

            # Print the configuration
            parsed_final_config = parse_config(config_data)
            print("E22 Module Configuration:")
            for key, value in parsed_final_config.items():
                print(f"{key}: {value}")
            print(f"Raw Config: {config_data.hex(' ').upper()}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
