#!/usr/bin/python3
import serial
import time
import argparse
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description="Send test messages via E22 LoRa module")
    parser.add_argument("--port", default="/dev/ttyUSB0", help="Serial port")
    parser.add_argument("--interval", type=float, default=5.0, help="Interval between messages in seconds (default: 5)")
    parser.add_argument("--message", default="Test", help="Base message to send (default: 'Test')")
    args = parser.parse_args()

    print(f"Starting continuous transmission test on {args.port}")
    print(f"Note: Using current E22 module configuration (check with ./e22.py)")
    print(f"Interval: {args.interval} seconds")
    print(f"Press Ctrl+C to stop\n")

    counter = 0

    try:
        with serial.Serial(args.port, baudrate=9600, timeout=1) as ser:
            while True:
                counter += 1
                timestamp = datetime.now().strftime("%H:%M:%S")
                message = f"{args.message} #{counter} {timestamp}\n"

                # Send message
                ser.write(message.encode('utf-8'))
                print(f"[{timestamp}] Sent: {message.strip()}")

                # Check for any received data
                time.sleep(0.1)
                if ser.in_waiting > 0:
                    received = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                    print(f"[{timestamp}] Received: {received.strip()}")

                # Wait before next transmission
                time.sleep(args.interval)

    except KeyboardInterrupt:
        print(f"\n\nTest stopped. Total messages sent: {counter}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
