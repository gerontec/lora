#!/usr/bin/env python3
"""
LoRa Send Script for E22 Module
Sends test packets via E22-900T USB module in Transparent Mode

Features:
- Regular packet transmission
- RSSI monitoring
- Packet counter
- Configurable interval
- Status logging
"""

import serial
import logging
import time
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Also log to file
file_handler = logging.FileHandler('/tmp/lorasend.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
logging.getLogger().addHandler(file_handler)


class E22Sender:
    """E22 LoRa Module Sender"""

    def __init__(self, port='/dev/ttyUSB0', baudrate=9600):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.packet_count = 0
        self.rssi_enabled = False

    def setup_serial(self):
        """Initialize serial connection"""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=1
            )
            logging.info(f"Serial port {self.port} opened successfully")
            time.sleep(0.5)  # Give E22 time to initialize
            return True
        except serial.SerialException as e:
            logging.error(f"Error opening serial port: {e}")
            return False

    def send_rssi_command(self):
        """Send RSSI query command to E22"""
        rssi_command = b'\xC0\xC1\xC2\xC3\x00\x02'
        self.ser.write(rssi_command)
        logging.debug(f"Sent RSSI query: {rssi_command.hex().upper()}")

        # Wait for response
        time.sleep(0.1)
        if self.ser.in_waiting > 0:
            response = self.ser.read(self.ser.in_waiting)
            rssi_value = self.process_rssi_response(response)
            if rssi_value is not None:
                logging.info(f"Current RSSI: {rssi_value} dBm")
                return rssi_value
        return None

    def process_rssi_response(self, response):
        """Process RSSI response from E22"""
        if len(response) >= 4 and response[0] == 0xC1:
            rssi_value = response[3]
            return -(256 - rssi_value)
        return None

    def send_packet(self, message):
        """Send a packet via E22 in Transparent Mode"""
        try:
            # In transparent mode, just write the data
            # E22 will transmit it immediately over LoRa
            encoded_msg = message.encode('utf-8')

            # Send the message
            self.ser.write(encoded_msg)

            # Add small delay to ensure transmission
            time.sleep(0.1)

            self.packet_count += 1
            timestamp = datetime.now().strftime("%H:%M:%S")

            print(f"[{timestamp}] Sent packet #{self.packet_count}: {message}")
            logging.info(f"TX Packet #{self.packet_count}: {message} ({len(encoded_msg)} bytes)")

            return True

        except Exception as e:
            logging.error(f"Error sending packet: {e}")
            return False

    def run(self, interval=5, message_prefix="TEST", enable_rssi=False):
        """Main send loop"""
        print("=" * 60)
        print("E22 LoRa Sender")
        print("=" * 60)
        print(f"Port:      {self.port}")
        print(f"Baudrate:  {self.baudrate}")
        print(f"Interval:  {interval} seconds")
        print(f"RSSI:      {'Enabled' if enable_rssi else 'Disabled'}")
        print("=" * 60)
        print()

        if not self.setup_serial():
            return

        print("Starting transmission... Press Ctrl+C to stop\n")

        try:
            while True:
                # Create message with timestamp
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                message = f"{message_prefix} #{self.packet_count + 1} {timestamp}\n"

                # Send packet
                self.send_packet(message)

                # Query RSSI every 10th packet
                if enable_rssi and (self.packet_count % 10 == 0):
                    self.send_rssi_command()

                # Wait before next transmission
                time.sleep(interval)

        except KeyboardInterrupt:
            print(f"\n\nStopped by user")
            print(f"Total packets sent: {self.packet_count}")
            logging.info(f"Session ended. Total packets: {self.packet_count}")

        except Exception as e:
            logging.error(f"Error in main loop: {e}")

        finally:
            if self.ser:
                self.ser.close()
                logging.info("Serial port closed")


def main():
    parser = argparse.ArgumentParser(
        description="E22 LoRa Module Sender - Send test packets via E22-900T"
    )
    parser.add_argument(
        "--port",
        default="/dev/ttyUSB0",
        help="Serial port (default: /dev/ttyUSB0)"
    )
    parser.add_argument(
        "--baudrate",
        type=int,
        default=9600,
        help="Baud rate (default: 9600)"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=5.0,
        help="Interval between packets in seconds (default: 5)"
    )
    parser.add_argument(
        "--message",
        default="TEST",
        help="Message prefix (default: 'TEST')"
    )
    parser.add_argument(
        "--rssi",
        action="store_true",
        help="Enable RSSI monitoring (queries every 10 packets)"
    )
    parser.add_argument(
        "--burst",
        type=int,
        help="Send N packets and exit (instead of continuous)"
    )

    args = parser.parse_args()

    sender = E22Sender(port=args.port, baudrate=args.baudrate)

    if args.burst:
        # Burst mode: send N packets and exit
        if not sender.setup_serial():
            return

        print(f"Burst mode: Sending {args.burst} packets...")
        for i in range(args.burst):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"{args.message} #{i + 1} {timestamp}\n"
            sender.send_packet(message)
            if i < args.burst - 1:  # Don't wait after last packet
                time.sleep(args.interval)

        print(f"\nBurst complete. Sent {args.burst} packets.")
        sender.ser.close()
    else:
        # Continuous mode
        sender.run(
            interval=args.interval,
            message_prefix=args.message,
            enable_rssi=args.rssi
        )


if __name__ == "__main__":
    main()
