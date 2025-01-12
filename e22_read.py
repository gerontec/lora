#!/usr/bin/python3
import serial
import time

ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)

def send_command_and_read(command):
    ser.write(command)
    time.sleep(0.1)
    return ser.read(100)

def interpret_register(register, value):
    interpretations = {
        0x00: f"ADDH: 0x{value:02X} - Module Address High Byte",
        0x01: f"ADDL: 0x{value:02X} - Module Address Low Byte",
        0x02: f"NETID: 0x{value:02X} - Network ID",
        0x03: f"REG0: 0x{value:02X} - UART and Air Speed Settings",
        0x04: f"REG1: 0x{value:02X} - Sub-packet and RSSI Settings",
        0x05: f"REG2: 0x{value:02X} - Channel Control",
        0x06: f"REG3: 0x{value:02X} - Transmission Options",
        0x07: f"CRYPT_H: 0x{value:02X} - Encryption Key High Byte (Write-only)",
        0x08: f"CRYPT_L: 0x{value:02X} - Encryption Key Low Byte (Write-only)"
    }
    return interpretations.get(register, f"Unknown Register: 0x{value:02X}")

start_address = 0x00
length = 0x09  # Reading 9 registers (00H to 08H)

command = bytearray([0xC1, start_address, length])
print(f"Sending command: {command.hex().upper()}")

response = send_command_and_read(command)
print(f"Response: {response.hex().upper()}")

if len(response) >= 12:
    header = response[:3]
    data = response[3:]
    print(f"Header: {header.hex().upper()}")
    print(f"Data: {data.hex().upper()}")
    
    print("\nRegister Interpretations:")
    for i, value in enumerate(data):
        interpretation = interpret_register(i, value)
        print(f"Register {i:02X}H: {interpretation}")
        
        if i == 0x03:
            uart_baud = ["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"][(value >> 5) & 0x07]
            uart_parity = ["8N1", "8O1", "8E1", "8N1"][(value >> 3) & 0x03]
            air_speed = ["2.4k", "2.4k", "2.4k", "2.4k", "4.8k", "9.6k", "15.6k", "15.6k"][value & 0x07]
            print(f"  - UART Baud Rate: {uart_baud} bps")
            print(f"  - UART Parity: {uart_parity}")
            print(f"  - Air Speed: {air_speed} bps")
        elif i == 0x04:
            sub_packet = ["240 bytes", "128 bytes", "64 bytes", "32 bytes"][(value >> 6) & 0x03]
            rssi_ambient = "Enabled" if value & 0x20 else "Disabled"
            software_mode = "Enabled" if value & 0x04 else "Disabled"
            tx_power = ["22dBm", "17dBm", "13dBm", "10dBm"][value & 0x03]
            print(f"  - Sub-packet size: {sub_packet}")
            print(f"  - RSSI Ambient Noise: {rssi_ambient}")
            print(f"  - Software Mode Switching: {software_mode}")
            print(f"  - Transmitting Power: {tx_power}")
        elif i == 0x05:
            print(f"  - Channel: {value}")
            print(f"    E22-230T22U: {220.125 + value * 0.25:.3f} MHz")
            print(f"    E22-400T22U: {410.125 + value:.3f} MHz")
            print(f"    E22-900T22U: {850.125 + value:.3f} MHz")
        elif i == 0x06:
            rssi_byte = "Enabled" if value & 0x80 else "Disabled"
            transmission = "Fixed-point" if value & 0x40 else "Transparent"
            relay = "Enabled" if value & 0x20 else "Disabled"
            lbt = "Enabled" if value & 0x10 else "Disabled"
            print(f"  - RSSI Byte: {rssi_byte}")
            print(f"  - Transmission Method: {transmission}")
            print(f"  - Relay Function: {relay}")
            print(f"  - LBT (Listen Before Talk): {lbt}")
else:
    print("Received response is shorter than expected.")

ser.close()
