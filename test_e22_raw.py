#!/usr/bin/env python3
"""Test E22 communication at low level"""
import serial
import time
import sys

port = '/dev/ttyUSB0'
baudrate = 9600

print("=" * 70)
print("E22 RAW COMMUNICATION TEST")
print("=" * 70)
print()
print("IMPORTANT: Module MUST be in Configuration Mode!")
print("  M0 = LOW  (GND)")
print("  M1 = HIGH (3.3V)")
print()
print("=" * 70)
print()

try:
    ser = serial.Serial(port, baudrate, timeout=2)
    time.sleep(0.2)
    ser.reset_input_buffer()

    print(f"✓ Connected to {port} at {baudrate} baud")
    print()

    # Test 1: Read Configuration (C1)
    print("Test 1: Read Configuration (0xC1 0x00 0x09)")
    print("-" * 70)
    cmd = bytes([0xC1, 0x00, 0x09])
    print(f"TX: {cmd.hex(' ').upper()}")
    ser.write(cmd)
    time.sleep(0.3)

    response = ser.read(100)
    print(f"RX: {response.hex(' ').upper()}")
    print(f"RX Length: {len(response)} bytes")

    if len(response) >= 12:
        print("✓ Valid config response!")
        print(f"  ADDH:  0x{response[3]:02X}")
        print(f"  ADDL:  0x{response[4]:02X}")
        print(f"  NETID: 0x{response[5]:02X}")
        print(f"  REG0:  0x{response[6]:02X}")
        print(f"  REG1:  0x{response[7]:02X}")
        print(f"  REG2:  0x{response[8]:02X}")
        print(f"  REG3:  0x{response[9]:02X}")
    else:
        print("✗ Invalid or no response")
        if len(response) > 0:
            print("  Possible issues:")
            print("  - Module not in Config Mode (check M0/M1 pins)")
            print("  - Wrong baudrate")
            print("  - Wrong module type")

    print()
    time.sleep(0.5)
    ser.reset_input_buffer()

    # Test 2: Read Version (C3)
    print("Test 2: Read Version (0xC3 0x00 0x00)")
    print("-" * 70)
    cmd = bytes([0xC3, 0x00, 0x00])
    print(f"TX: {cmd.hex(' ').upper()}")
    ser.write(cmd)
    time.sleep(0.3)

    response = ser.read(100)
    print(f"RX: {response.hex(' ').upper()}")
    print(f"RX Length: {len(response)} bytes")

    if len(response) >= 4 and response[0] == 0xC1:
        print("✓ Valid version response!")
        freq_map = {
            0x32: '433MHz',
            0x38: '470MHz',
            0x45: '868MHz',
            0x44: '915MHz',
            0x46: '170MHz'
        }
        if len(response) >= 5:
            freq = freq_map.get(response[4], f'Unknown (0x{response[4]:02X})')
            print(f"  Frequency: {freq}")
    else:
        print("✗ Invalid version response")
        if response[:3] == cmd:
            print("  ⚠ Module is ECHOING the command!")
            print("  ⚠ Module is likely NOT in Configuration Mode")
            print("  ⚠ Set M0=LOW, M1=HIGH and try again")

    print()
    print("=" * 70)
    print("TROUBLESHOOTING:")
    print("=" * 70)
    print("If you see ECHO (command echoed back):")
    print("  1. Module is in Normal/WOR mode, not Config mode")
    print("  2. Set M0=LOW (GND), M1=HIGH (3.3V)")
    print("  3. Power cycle the module")
    print("  4. Try again")
    print()
    print("If you see no response:")
    print("  1. Check wiring (TX/RX swapped?)")
    print("  2. Check baudrate (try 9600)")
    print("  3. Check power (3.3V-5V)")
    print()

    ser.close()

except serial.SerialException as e:
    print(f"✗ Serial Error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
