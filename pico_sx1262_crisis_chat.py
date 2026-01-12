"""
Crisis Chat für Raspberry Pi Pico W + SX1262 LoRa HAT
Waveshare Pico-LoRa-SX1262-868M

Hardware:
  - Raspberry Pi Pico W
  - Waveshare Pico-LoRa-SX1262-868M HAT
  - Frequenz: 868 MHz (EU868)
  - Chip: Semtech SX1262

Features:
  - NetID-basiertes Routing (kompatibel mit crisis_chat.py)
  - Custom Sync Word (0x11)
  - Backhaul-Filter
  - Broadcast und Unicast Support
  - WiFi + LoRa Gateway Funktion

Installation:
  1. Flash MicroPython auf Pico W:
     https://micropython.org/download/rp2-pico-w/

  2. Installiere sx1262 Library:
     import mip
     mip.install('github:ehong-tl/micropySX126X')

  3. Kopiere dieses Script auf Pico

  4. Anpassen:
     - MY_NETID
     - MY_ADDR
     - USERNAME

Usage:
  # Terminal (Thonny IDE oder rshell)
  >>> import pico_sx1262_crisis_chat
  >>> chat = CrisisChatPico("Alice", netid=0x0034)
  >>> chat.send_broadcast("Hilfe benötigt!")
  >>> chat.listen()
"""

from sx1262 import SX1262
import struct
import time
from machine import Pin

# ===== KONFIGURATION =====

# Waveshare Pico-LoRa-SX1262-868M Pin Mapping
LORA_PINS = {
    'spi_bus': 1,
    'clk': 10,      # GP10 - SCK
    'mosi': 11,     # GP11 - MOSI
    'miso': 12,     # GP12 - MISO
    'cs': 3,        # GP3  - NSS/CS
    'irq': 20,      # GP20 - DIO1
    'rst': 15,      # GP15 - RESET
    'gpio': 2       # GP2  - BUSY
}

# LoRa Parameter (kompatibel mit E22 Default & Crisis Chat)
LORA_CONFIG = {
    'freq': 868.1,        # MHz - E22 Channel 17
    'bw': 125.0,          # kHz - Bandwidth
    'sf': 9,              # Spreading Factor (2.4k air rate)
    'cr': 7,              # Coding Rate 4/7
    'syncWord': 0x11,     # Custom Sync Word (ändere zu 0x12 für E22 Default)
    'power': 22,          # dBm TX Power
    'preambleLength': 8,
    'crcOn': True
}

# Netzwerk-Konfiguration
MY_NETID = 0x0034   # Dein Network ID
MY_ADDR = 0x2001    # Deine Node Address (ändern!)

# ===== CRISIS CHAT CLASS =====

class CrisisChatPico:
    """Crisis Chat Implementierung für Pico + SX1262"""

    def __init__(self, username, netid=0x0034, addr=None, channel="emergency"):
        self.username = username[:20]
        self.netid = netid
        self.addr = addr if addr else MY_ADDR
        self.channel = channel[:20]

        # Message History (Backhaul Filter)
        self.sent_messages = []
        self.max_history = 50

        # Statistics
        self.tx_count = 0
        self.rx_count = 0
        self.rx_filtered = 0

        # Init LoRa
        print("Initializing SX1262...")
        self.sx = SX1262(**LORA_PINS)

        self.sx.begin(
            freq=LORA_CONFIG['freq'],
            bw=LORA_CONFIG['bw'],
            sf=LORA_CONFIG['sf'],
            cr=LORA_CONFIG['cr'],
            syncWord=LORA_CONFIG['syncWord'],
            power=LORA_CONFIG['power'],
            currentLimit=140.0,
            preambleLength=LORA_CONFIG['preambleLength'],
            implicit=False,
            implicitLen=0xFF,
            crcOn=LORA_CONFIG['crcOn'],
            txIq=False,
            rxIq=False,
            tcxoVoltage=1.7,
            useRegulatorLDO=False,
            blocking=True
        )

        # LED (GP25 - onboard LED)
        self.led = Pin("LED", Pin.OUT)
        self.led.off()

        print(f"✓ Crisis Chat initialized")
        print(f"  NetID:    0x{self.netid:04X}")
        print(f"  Address:  0x{self.addr:04X}")
        print(f"  Username: {self.username}")
        print(f"  Channel:  {self.channel}")
        print(f"  Sync:     0x{LORA_CONFIG['syncWord']:02X}")
        print(f"  Freq:     {LORA_CONFIG['freq']} MHz")

    def format_message(self, text):
        """
        Paket-Format (kompatibel mit crisis_chat.py):
        [NetID:2][SrcAddr:2][DstAddr:2][Channel:20][Username:20][Text:max 207]

        Max LoRa Payload: 255 bytes
        Header: 2+2+2+20+20 = 46 bytes
        Max Text: 255-46 = 209 bytes (nutzen 207 für Sicherheit)
        """
        # Limit text
        text = text[:207]

        # Build channel and username (fixed 20 bytes)
        channel_bytes = self.channel.encode()[:20].ljust(20, b'\x00')
        username_bytes = self.username.encode()[:20].ljust(20, b'\x00')

        # Build text
        text_bytes = text.encode() if isinstance(text, str) else text

        return channel_bytes + username_bytes + text_bytes

    def send_message(self, dst_addr, text):
        """Sende Nachricht an Ziel-Adresse (0xFFFF = Broadcast)"""

        # Build header + payload
        header = struct.pack('>HHH', self.netid, self.addr, dst_addr)
        payload = self.format_message(text)
        packet = header + payload

        # Check size
        if len(packet) > 255:
            print(f"ERROR: Packet too large ({len(packet)} bytes)")
            return False

        # LED on during TX
        self.led.on()

        # Send
        try:
            self.sx.send(list(packet))

            # Remember for backhaul filter
            self.sent_messages.append(packet)
            if len(self.sent_messages) > self.max_history:
                self.sent_messages.pop(0)

            self.tx_count += 1

            dst_str = "ALL" if dst_addr == 0xFFFF else f"{dst_addr:04X}"
            print(f"[TX→{dst_str}] {text[:50]}")

            return True

        except Exception as e:
            print(f"TX Error: {e}")
            return False

        finally:
            self.led.off()

    def send_broadcast(self, text):
        """Broadcast Nachricht (wie CB-Funk)"""
        return self.send_message(0xFFFF, text)

    def send_to(self, dst_addr, text):
        """Unicast Nachricht an spezifische Adresse"""
        return self.send_message(dst_addr, text)

    def parse_packet(self, packet_bytes):
        """Parse empfangenes Paket"""
        packet = bytes(packet_bytes)

        # Minimum size check
        if len(packet) < 46:
            return None

        # Parse header
        netid, src_addr, dst_addr = struct.unpack('>HHH', packet[:6])

        # Parse payload
        channel_bytes = packet[6:26]
        username_bytes = packet[26:46]
        text_bytes = packet[46:]

        # Decode strings (remove null padding)
        channel = channel_bytes.rstrip(b'\x00').decode('utf-8', errors='ignore')
        username = username_bytes.rstrip(b'\x00').decode('utf-8', errors='ignore')
        text = text_bytes.decode('utf-8', errors='ignore')

        return {
            'netid': netid,
            'src': src_addr,
            'dst': dst_addr,
            'channel': channel,
            'username': username,
            'text': text,
            'raw': packet
        }

    def on_receive(self, packet_bytes):
        """Callback für empfangene Pakete"""

        # LED blink
        self.led.on()

        try:
            # Parse
            msg = self.parse_packet(packet_bytes)
            if not msg:
                print("[RX] Invalid packet (too short)")
                return

            # Backhaul filter
            if msg['raw'] in self.sent_messages:
                self.rx_filtered += 1
                print(f"[RX] Backhaul filtered (own message)")
                return

            # NetID filter
            if msg['netid'] != self.netid:
                self.rx_filtered += 1
                print(f"[RX] Wrong NetID: {msg['netid']:04X} (expected {self.netid:04X})")
                return

            # Address filter
            if msg['dst'] != self.addr and msg['dst'] != 0xFFFF:
                self.rx_filtered += 1
                # Silent drop (nicht für uns)
                return

            # Valid message!
            self.rx_count += 1

            dst_str = "ALL" if msg['dst'] == 0xFFFF else f"ME({self.addr:04X})"
            print(f"[{msg['channel']}][{msg['username']}→{dst_str}] {msg['text']}")

        except Exception as e:
            print(f"RX Error: {e}")

        finally:
            self.led.off()

    def listen(self, duration=None):
        """
        Höre auf eingehende Nachrichten

        Args:
            duration: Sekunden (None = unendlich)
        """
        print(f"\n{'='*50}")
        print(f"Listening on NetID {self.netid:04X}, Channel '{self.channel}'")
        print(f"Press Ctrl+C to stop")
        print(f"{'='*50}\n")

        # Set callback
        self.sx.setBlockingCallback(False, self.on_receive)

        start = time.time()

        try:
            while True:
                # Check duration
                if duration and (time.time() - start) > duration:
                    break

                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\nStopped by user")

        finally:
            print(f"\nStatistics:")
            print(f"  TX: {self.tx_count}")
            print(f"  RX: {self.rx_count}")
            print(f"  Filtered: {self.rx_filtered}")

    def interactive(self):
        """Interaktiver Chat-Modus"""
        print(f"\n{'='*50}")
        print(f"Crisis Chat - Interactive Mode")
        print(f"NetID: {self.netid:04X} | Addr: {self.addr:04X} | User: {self.username}")
        print(f"{'='*50}")
        print(f"Commands:")
        print(f"  <text>        - Broadcast message")
        print(f"  @<addr> <msg> - Send to specific address")
        print(f"  /stats        - Show statistics")
        print(f"  /quit         - Exit")
        print(f"{'='*50}\n")

        # Start listening in background
        self.sx.setBlockingCallback(False, self.on_receive)

        try:
            while True:
                try:
                    line = input(f"{self.username}> ")

                    if not line:
                        continue

                    if line == "/quit":
                        break

                    if line == "/stats":
                        print(f"TX: {self.tx_count}, RX: {self.rx_count}, Filtered: {self.rx_filtered}")
                        continue

                    # Unicast?
                    if line.startswith('@'):
                        parts = line[1:].split(' ', 1)
                        if len(parts) == 2:
                            try:
                                addr = int(parts[0], 16)
                                self.send_to(addr, parts[1])
                            except ValueError:
                                print("Invalid address (use hex: @1234 message)")
                        else:
                            print("Usage: @<addr> <message>")
                    else:
                        # Broadcast
                        self.send_broadcast(line)

                except EOFError:
                    break

        except KeyboardInterrupt:
            print("\nExiting...")

        print(f"\nFinal stats: TX={self.tx_count}, RX={self.rx_count}")

# ===== MAIN =====

def main():
    """Hauptfunktion"""
    import sys

    # Default config
    username = "Pico"
    netid = MY_NETID
    addr = MY_ADDR

    # Parse args (wenn von Shell gestartet)
    if len(sys.argv) > 1:
        username = sys.argv[1]
    if len(sys.argv) > 2:
        netid = int(sys.argv[2], 0)
    if len(sys.argv) > 3:
        addr = int(sys.argv[3], 0)

    # Create chat
    chat = CrisisChatPico(username, netid=netid, addr=addr)

    # Test message
    chat.send_broadcast(f"Hello from {username}!")

    # Interactive mode
    chat.interactive()

# ===== RUN =====

if __name__ == "__main__":
    main()

# ===== QUICK TEST EXAMPLES =====

"""
# Test 1: Simple Broadcast
>>> from pico_sx1262_crisis_chat import CrisisChatPico
>>> chat = CrisisChatPico("Alice", netid=0x0034, addr=0x2001)
>>> chat.send_broadcast("Test message!")
>>> chat.listen(duration=30)  # Listen 30 seconds

# Test 2: Unicast
>>> chat.send_to(0x2002, "Hello Bob!")

# Test 3: Interactive Chat
>>> chat.interactive()
Alice> Hello everyone!
Alice> @2002 Private message to Bob
Alice> /stats
Alice> /quit

# Test 4: Different Channel
>>> chat2 = CrisisChatPico("Bob", netid=0x0034, addr=0x2002, channel="status")
>>> chat2.send_broadcast("Status update")
"""
