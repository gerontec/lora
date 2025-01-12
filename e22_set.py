#!/usr/bin/python3
import serial
import time
import argparse

def send_command_and_read(ser, command):
    ser.write(command)
    time.sleep(0.1)
    return ser.read(100)

def set_parameters(ser, args):
    # Construct REG0
    reg0 = (args.uart_baud << 5) | (args.uart_parity << 3) | args.air_speed

    # Construct REG1
    reg1 = (args.sub_packet << 6) | (args.rssi_noise << 5) | (args.mode_switch << 2) | args.tx_power

    # Construct REG3
    reg3 = (args.rssi_byte << 7) | (args.transmission << 6) | (args.relay << 5) | (args.lbt << 4)

    # Construct command
    command = bytearray([0xCF, 0xCF, 0xC0, 0x00, 0x09])
    command.extend([args.addh, args.addl, args.netid, reg0, reg1, args.channel, reg3, args.crypt_h, args.crypt_l])

    response = send_command_and_read(ser, command)
    print(f"Set parameters response: {response.hex().upper()}")

def main():
    parser = argparse.ArgumentParser(description="Configure E22 LoRa module")
    parser.add_argument("--addh", type=int, default=0, help="ADDH (0-255)")
    parser.add_argument("--addl", type=int, default=0, help="ADDL (0-255)")
    parser.add_argument("--netid", type=int, default=0, help="NETID (0-255)")
    parser.add_argument("--uart-baud", type=int, default=3, help="UART Baud Rate (0-7)")
    parser.add_argument("--uart-parity", type=int, default=0, help="UART Parity (0-3)")
    parser.add_argument("--air-speed", type=int, default=2, help="Air Speed (0-7)")
    parser.add_argument("--sub-packet", type=int, default=0, help="Sub-packet size (0-3)")
    parser.add_argument("--rssi-noise", type=int, default=0, help="RSSI Ambient Noise (0-1)")
    parser.add_argument("--mode-switch", type=int, default=0, help="Software Mode Switching (0-1)")
    parser.add_argument("--tx-power", type=int, default=0, help="Transmitting Power (0-3)")
    parser.add_argument("--channel", type=int, required=True, help="Channel (0-83)")
    parser.add_argument("--rssi-byte", type=int, default=0, help="Enable RSSI Byte (0-1)")
    parser.add_argument("--transmission", type=int, default=0, help="Transmission Method (0-1)")
    parser.add_argument("--relay", type=int, default=0, help="Relay Function (0-1)")
    parser.add_argument("--lbt", type=int, default=0, help="LBT Enable (0-1)")
    parser.add_argument("--crypt-h", type=int, default=0, help="Encryption Key High Byte (0-255)")
    parser.add_argument("--crypt-l", type=int, default=0, help="Encryption Key Low Byte (0-255)")
    args = parser.parse_args()

    ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
    set_parameters(ser, args)
    ser.close()

if __name__ == "__main__":
    main()
