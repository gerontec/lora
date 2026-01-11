#!/usr/bin/env python3
"""
LoRa Timing Test - Measure LBT and transmission delays
"""
import serial
import time
import sys

def setup_serial():
    try:
        ser = serial.Serial(
            port='/dev/ttyUSB0',
            baudrate=9600,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=0.1  # Short timeout for precise timing
        )
        return ser
    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
        return None

def measure_roundtrip(ser, test_msg="TEST", iterations=10):
    """
    Measure time from send to receive (via repeater backhaul)
    """
    print(f"\n{'='*60}")
    print(f"Testing roundtrip time for message: '{test_msg}'")
    print(f"Iterations: {iterations}")
    print(f"{'='*60}\n")

    delays = []

    for i in range(iterations):
        # Clear input buffer
        ser.reset_input_buffer()

        # Send message
        msg = f"{test_msg}_{i:03d}\r\n"
        t_start = time.time()
        ser.write(msg.encode('utf-8'))
        print(f"[{i+1:02d}] Sent at {t_start:.3f}: {msg.strip()}")

        # Wait for echo back (via repeater)
        received = False
        timeout = 5.0  # 5 second timeout
        t_timeout = time.time() + timeout
        buffer = bytearray()

        while time.time() < t_timeout:
            data = ser.read(100)
            if data:
                buffer.extend(data)

                # Check if we received our message back
                if msg.encode('utf-8').strip() in buffer:
                    t_end = time.time()
                    delay = (t_end - t_start) * 1000  # Convert to ms
                    delays.append(delay)
                    print(f"     Received at {t_end:.3f}: {msg.strip()}")
                    print(f"     ⏱️  Roundtrip: {delay:.1f}ms\n")
                    received = True
                    break

        if not received:
            print(f"     ❌ Timeout - no echo received\n")

        # Wait before next iteration
        time.sleep(2)

    # Statistics
    if delays:
        print(f"\n{'='*60}")
        print(f"RESULTS ({len(delays)} successful measurements):")
        print(f"{'='*60}")
        print(f"Min delay:     {min(delays):7.1f}ms")
        print(f"Max delay:     {max(delays):7.1f}ms")
        print(f"Average delay: {sum(delays)/len(delays):7.1f}ms")
        print(f"{'='*60}\n")

        # Analyze delays
        avg_delay = sum(delays) / len(delays)
        expected_airtime = 100  # ~80-100ms for small packet at 1200bps

        print("ANALYSIS:")
        print(f"Expected air-time (both ways):  ~{expected_airtime*2}ms")
        print(f"Measured average delay:         {avg_delay:.1f}ms")
        print(f"Extra delay (LBT + processing): {avg_delay - expected_airtime*2:.1f}ms")

        if avg_delay > 1000:
            print(f"\n⚠️  WARNING: >1 second delay detected!")
            print(f"   Possible causes:")
            print(f"   - LBT waiting for channel (heavy traffic)")
            print(f"   - Software delays in receiver")
            print(f"   - Multiple repeater hops")
            print(f"   - Low data rate (check air baud rate)")
    else:
        print("\n❌ No successful measurements!")

def main():
    print("LoRa Timing Test")
    print("=" * 60)

    ser = setup_serial()
    if ser is None:
        return

    try:
        # Test 1: Short messages
        measure_roundtrip(ser, test_msg="PING", iterations=5)

        # Test 2: Longer messages
        measure_roundtrip(ser, test_msg="LONGER_MESSAGE_TEST", iterations=5)

    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        ser.close()

if __name__ == "__main__":
    main()
