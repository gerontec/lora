#!/usr/bin/python3
"""Quick test to detect E22 module model"""
import serial
import time
import sys

def send_command(ser, command, desc=""):
    """Send command and show response"""
    print(f"\n{desc}")
    print(f"  Sending: {command.hex().upper()}")
    ser.write(command)
    time.sleep(0.2)
    response = ser.read(100)
    print(f"  Received: {response.hex().upper()} ({len(response)} bytes)")
    return response

try:
    port = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"
    print(f"Testing E22 module on {port}")
    print("="*60)

    with serial.Serial(port, baudrate=9600, timeout=1) as ser:
        time.sleep(0.1)

        # Test 1: Read configuration (C1 command)
        response = send_command(ser, bytes([0xC1, 0x00, 0x09]), "1. Configuration read (C1 00 09):")

        # Test 2: Read product info (C1 80 07)
        response = send_command(ser, bytes([0xC1, 0x80, 0x07]), "2. Product info (C1 80 07):")

        # Test 3: Version command (C3 C3 C3)
        response = send_command(ser, bytes([0xC3, 0xC3, 0xC3]), "3. Version command (C3 C3 C3):")

        # Test 4: Alternative version (C1 80 01)
        response = send_command(ser, bytes([0xC1, 0x80, 0x01]), "4. Alternative version (C1 80 01):")

        print("\n" + "="*60)
        print("Test complete. Please share all outputs above.")

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
