#!/usr/bin/env python3
"""
Crisis Communication Chat - Based on Höchst et al. 2020
Simple public message board for emergency communication

Usage:
    ./crisis_chat.py --username "John" --channel emergency
"""

import serial
import time
import argparse
import sys
from datetime import datetime
from collections import deque

class CrisisChat:
    """
    Simple LoRa-based crisis communication chat
    Based on public message board paradigm (like Twitter/CB-Funk)
    """

    def __init__(self, username, channel="emergency", port='/dev/ttyUSB0', baudrate=9600):
        self.username = username[:20]  # Max 20 chars
        self.channel = channel[:20]
        self.port = port
        self.baudrate = baudrate
        self.ser = None

        # Message tracking (prevent backhaul echo)
        self.sent_messages = deque(maxlen=50)
        self.message_history = []

        # Timing for send intervals
        self.last_send = 0
        self.min_send_interval = 60  # 60 seconds minimum (Duty Cycle)

    def connect(self):
        """Connect to LoRa module"""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=0.1  # Non-blocking
            )
            print(f"✓ Connected to {self.port}")
            return True
        except serial.SerialException as e:
            print(f"✗ Error connecting to {self.port}: {e}")
            return False

    def format_message(self, text):
        """
        Format message according to simple pipe protocol
        Format: channel|username|timestamp|message
        Max 50 chars for message to keep air-time low
        """
        timestamp = datetime.now().strftime("%H:%M")
        text = text[:50]  # Limit to 50 chars
        msg = f"{self.channel}|{self.username}|{timestamp}|{text}"
        return msg

    def parse_message(self, raw):
        """Parse incoming message"""
        try:
            parts = raw.strip().split('|')
            if len(parts) >= 4:
                return {
                    'channel': parts[0],
                    'username': parts[1],
                    'timestamp': parts[2],
                    'message': '|'.join(parts[3:])  # In case message contains |
                }
        except:
            pass
        return None

    def send_message(self, text):
        """Send message with duty cycle check"""
        now = time.time()

        # Check duty cycle
        time_since_last = now - self.last_send
        if time_since_last < self.min_send_interval:
            wait_time = self.min_send_interval - time_since_last
            print(f"⏳ Duty Cycle: Wait {wait_time:.0f}s before sending")
            return False

        # Format and send
        msg = self.format_message(text)

        # Check length (max 240 bytes for LoRa)
        if len(msg) > 240:
            print(f"✗ Message too long ({len(msg)} bytes, max 240)")
            return False

        try:
            self.ser.write((msg + "\r\n").encode('utf-8'))
            self.sent_messages.append(msg)
            self.last_send = now
            print(f"📤 [{self.username}] {text}")
            return True
        except Exception as e:
            print(f"✗ Send error: {e}")
            return False

    def receive_messages(self):
        """Non-blocking receive with backhaul filter"""
        if not self.ser or not self.ser.in_waiting:
            return

        try:
            data = self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')

            for line in data.split('\n'):
                line = line.strip()
                if not line:
                    continue

                # Filter own messages (backhaul from repeater)
                if line in self.sent_messages:
                    continue

                # Parse message
                parsed = self.parse_message(line)
                if not parsed:
                    continue

                # Filter by channel
                if parsed['channel'] != self.channel:
                    continue

                # Display message
                self.display_message(parsed)

        except Exception as e:
            print(f"✗ Receive error: {e}")

    def display_message(self, msg):
        """Display received message"""
        prefix = "🔴" if "NOTFALL" in msg['message'].upper() else "💬"
        print(f"{prefix} [{msg['timestamp']}] {msg['username']}: {msg['message']}")
        self.message_history.append(msg)

    def interactive_mode(self):
        """Interactive chat mode"""
        print("\n" + "="*60)
        print(f"  CRISIS CHAT - Channel: #{self.channel}")
        print(f"  User: {self.username}")
        print("="*60)
        print("\nCommands:")
        print("  Type message and press Enter to send")
        print("  /help     - Show this help")
        print("  /status   - Send status update")
        print("  /notfall  - Send emergency message")
        print("  /quit     - Exit")
        print("\nListening for messages...\n")

        import select

        while True:
            # Non-blocking receive
            self.receive_messages()

            # Check for user input (non-blocking)
            if select.select([sys.stdin], [], [], 0.1)[0]:
                user_input = sys.stdin.readline().strip()

                if not user_input:
                    continue

                # Handle commands
                if user_input == '/quit':
                    print("👋 Goodbye!")
                    break

                elif user_input == '/help':
                    print("\n📋 Commands:")
                    print("  /status   - Send 'Status OK'")
                    print("  /notfall  - Send emergency alert")
                    print("  /quit     - Exit chat")
                    print()

                elif user_input == '/status':
                    self.send_message("Status OK")

                elif user_input == '/notfall':
                    emergency = input("Emergency message: ")
                    if emergency:
                        self.send_message(f"NOTFALL: {emergency}")

                else:
                    # Send regular message
                    self.send_message(user_input)

            # Small delay to prevent busy-waiting
            time.sleep(0.1)

    def status_beacon_mode(self, interval=600):
        """
        Send status beacon every X seconds (default 10 minutes)
        For battery-powered nodes
        """
        print(f"\n📡 Status Beacon Mode - Every {interval}s")
        print(f"Channel: #{self.channel}, User: {self.username}\n")

        while True:
            # Receive messages
            for _ in range(100):  # Check for 10 seconds
                self.receive_messages()
                time.sleep(0.1)

            # Send status
            self.send_message("Status OK")

            # Sleep until next beacon
            print(f"💤 Sleeping for {interval}s...")
            time.sleep(interval)

    def close(self):
        """Close serial connection"""
        if self.ser:
            self.ser.close()
            print("✓ Connection closed")

def main():
    parser = argparse.ArgumentParser(
        description='Crisis Communication Chat - Simple LoRa messaging',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Interactive mode:
    ./crisis_chat.py --username John --channel emergency

  Status beacon (battery mode):
    ./crisis_chat.py --username Node1 --channel status --beacon 600

  Send single message:
    ./crisis_chat.py --username John --channel emergency --send "Need water"
        """
    )

    parser.add_argument('--username', required=True, help='Your username (max 20 chars)')
    parser.add_argument('--channel', default='emergency', help='Channel name (default: emergency)')
    parser.add_argument('--port', default='/dev/ttyUSB0', help='Serial port')
    parser.add_argument('--baudrate', type=int, default=9600, help='Baud rate')
    parser.add_argument('--beacon', type=int, metavar='SECONDS', help='Status beacon mode (send every N seconds)')
    parser.add_argument('--send', metavar='MESSAGE', help='Send single message and exit')

    args = parser.parse_args()

    # Create chat instance
    chat = CrisisChat(
        username=args.username,
        channel=args.channel,
        port=args.port,
        baudrate=args.baudrate
    )

    # Connect
    if not chat.connect():
        sys.exit(1)

    try:
        if args.send:
            # Single message mode
            chat.send_message(args.send)
        elif args.beacon:
            # Beacon mode
            chat.status_beacon_mode(interval=args.beacon)
        else:
            # Interactive mode
            chat.interactive_mode()

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")

    finally:
        chat.close()

if __name__ == '__main__':
    main()
