#!/usr/bin/python3
"""
Remote LoRa Packet Monitor für Dragino Gateway
Läuft auf heissa.de und verbindet sich via SSH zum Dragino

Angepasst für E22 Default-Konfiguration:
  - Channel 17 → 867.1 MHz
  - Air Rate 2.4k → BW=125kHz, SF=9
  - Address: 0xFFFF, Network: 0x00
  - Baud: 9600, Power: 22dBm

Dragino Gateway Settings:
  - Radio Type: 1257 (SX1257)
  - Clock Source: 0 (Radio A)
  - Channel Mode: 1 (Same freq all channels)

Vorteile:
  - Kein Speicherplatz auf Dragino benötigt
  - Python-Parsing auf leistungsfähigem Server
  - Einfache MQTT-Integration
  - Besseres Logging und Fehlerbehandlung

Installation:
  1. SSH Key-Setup (ohne Password):
     ssh-copy-id root@10.0.0.2

  2. Script starten:
     python3 dragino_remote_monitor.py

Optional mit MQTT:
  python3 dragino_remote_monitor.py --mqtt
"""

import subprocess
import re
import sys
import time
from datetime import datetime
import argparse

# Optional: MQTT Support
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False

# Version
VERSION = "1.2.0"

# --- KONFIGURATION ---
DRAGINO_HOST = "10.0.0.2"
DRAGINO_USER = "root"

# E22 Default Config: Channel 17 = 867.1 MHz
FREQ_A = "867.1"  # E22 Channel 17 (Primary)
FREQ_B = "867.3"  # E22 Channel 19 (Backup/Scan)

# Dragino Gateway Configuration
# Radio type: 1257 for SX1257 (typical for LG308/LPS8)
RADIO_TYPE = 1257
CLOCK_SOURCE = 0  # Radio A as clock source
CHANNEL_MODE = 1  # Same frequency for all channels

# MQTT Konfiguration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "dragino-27e318/gateway1/data"


class LoRaPacket:
    """Repräsentiert ein empfangenes LoRa-Paket"""
    def __init__(self):
        self.freq_hz = None
        self.size = 0
        self.chan = None
        self.rssi = None
        self.snr = None
        self.data = None
        self.timestamp = None

    @property
    def freq_mhz(self):
        if self.freq_hz:
            return self.freq_hz / 1_000_000
        return None

    def is_valid(self):
        """Prüft ob Paket vollständige Daten hat"""
        return self.freq_hz is not None and self.size is not None

    def to_dict(self):
        """Konvertiert Paket zu Dictionary für MQTT"""
        return {
            "timestamp": self.timestamp,
            "freq_mhz": self.freq_mhz,
            "freq_hz": self.freq_hz,
            "size": self.size,
            "chan": self.chan,
            "rssi": self.rssi,
            "snr": self.snr,
            "has_payload": self.size > 0
        }

    def __str__(self):
        status = "✅ Payload received" if self.size > 0 else "⚠️  No payload"
        return f"""┌─ LoRa Packet ─────────────────────────────────
│ Time:      {self.timestamp}
│ Frequency: {self.freq_mhz:.1f} MHz (Channel {self.chan})
│ Size:      {self.size} bytes
│ RSSI:      {self.rssi} dBm
│ SNR:       {self.snr} dB
│ Status:    {status}
└────────────────────────────────────────────────"""


class DraginoMonitor:
    """Verbindet zu Dragino via SSH und monitort LoRa-Pakete"""

    def __init__(self, use_mqtt=False):
        self.packet_count = 0
        self.current_packet = None
        self.use_mqtt = use_mqtt
        self.mqtt_client = None

        if self.use_mqtt:
            if not MQTT_AVAILABLE:
                print("❌ MQTT requested but paho-mqtt not installed!")
                print("   Install: pip3 install paho-mqtt")
                sys.exit(1)
            self.setup_mqtt()

    def setup_mqtt(self):
        """Initialisiert MQTT-Verbindung"""
        print(f"🔌 Connecting to MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")
        self.mqtt_client = mqtt.Client()
        try:
            self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.mqtt_client.loop_start()
            print("✅ MQTT connected")
        except Exception as e:
            print(f"❌ MQTT connection failed: {e}")
            sys.exit(1)

    def publish_packet(self, packet):
        """Sendet Paket via MQTT"""
        if self.mqtt_client:
            import json
            payload = json.dumps(packet.to_dict())
            self.mqtt_client.publish(MQTT_TOPIC, payload)
            print(f"   📤 Published to MQTT: {MQTT_TOPIC}")

    def parse_line(self, line):
        """Parst eine Zeile von test_loragw_hal_rx"""

        # Neue Paket-Sektion beginnt
        if "----- LoRa packet -----" in line:
            self.current_packet = LoRaPacket()
            return

        if not self.current_packet:
            return

        # Parse verschiedene Felder
        if "freq_hz" in line:
            match = re.search(r'freq_hz\s+(\d+)', line)
            if match:
                self.current_packet.freq_hz = int(match.group(1))

        elif line.strip().startswith("size:"):
            match = re.search(r'size:\s+(\d+)', line)
            if match:
                self.current_packet.size = int(match.group(1))

        elif line.strip().startswith("chan:"):
            match = re.search(r'chan:\s+(\d+)', line)
            if match:
                self.current_packet.chan = int(match.group(1))

        elif "rssi_sig" in line:
            match = re.search(r'rssi_sig\s*:\s*([-\d.]+)', line)
            if match:
                self.current_packet.rssi = float(match.group(1))

        elif "snr_avg" in line:
            match = re.search(r'snr_avg:\s*([-\d.]+)', line)
            if match:
                self.current_packet.snr = float(match.group(1))

        # Paket komplett empfangen
        elif "Received" in line and "packets" in line:
            if self.current_packet and self.current_packet.is_valid():
                self.current_packet.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.packet_count += 1

                print(f"\n{self.current_packet}")

                if self.use_mqtt:
                    self.publish_packet(self.current_packet)

                self.current_packet = None

    def stop_dragino_services(self):
        """Stoppt interferierende Services auf Dragino"""
        print("🛑 Stopping Packet Forwarder on Dragino...")
        cmd = ["ssh", f"{DRAGINO_USER}@{DRAGINO_HOST}", "killall fwd 2>/dev/null; sleep 1"]
        subprocess.run(cmd, capture_output=True)

    def run(self, debug=False):
        """Hauptloop: Verbindet zu Dragino und monitort Pakete"""
        print("=" * 60)
        print(f"Remote LoRa Packet Monitor v{VERSION} (E22 Default Config)")
        print("=" * 60)
        print(f"Dragino:   {DRAGINO_USER}@{DRAGINO_HOST}")
        print(f"Frequency: {FREQ_A} MHz (Channel 17) and {FREQ_B} MHz")
        print(f"Radio:     SX{RADIO_TYPE} (Clock source: {CLOCK_SOURCE})")
        print(f"Mode:      {CHANNEL_MODE} (Same freq all channels)")
        print(f"MQTT:      {'Enabled' if self.use_mqtt else 'Disabled'}")
        if debug:
            print(f"Debug:     Enabled")
        print("=" * 60)
        print()

        # Stoppe interferierende Services
        self.stop_dragino_services()

        # SSH Kommando mit korrekten Parametern für Dragino Gateway
        cmd = [
            "ssh",
            f"{DRAGINO_USER}@{DRAGINO_HOST}",
            f"test_loragw_hal_rx -r {RADIO_TYPE} -a {FREQ_A} -b {FREQ_B} -k {CLOCK_SOURCE} -m {CHANNEL_MODE}"
        ]

        try:
            print(f"🔌 Connecting via SSH to {DRAGINO_HOST}...")
            print(f"   Command: test_loragw_hal_rx -r {RADIO_TYPE} -a {FREQ_A} -b {FREQ_B} -k {CLOCK_SOURCE} -m {CHANNEL_MODE}")

            # Starte SSH Prozess
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                universal_newlines=True
            )

            print("✅ Connected - monitoring packets...")
            print("   E22 Config: Ch17, 2.4k air rate, 9600 baud, 22dBm")
            print("   Press Ctrl+C to stop")
            print()

            line_count = 0
            # Lese Zeile für Zeile
            for line in process.stdout:
                line = line.strip()
                line_count += 1

                # Im Debug-Modus alle Zeilen anzeigen
                if debug:
                    print(f"[DEBUG {line_count}] {line}")

                if "Waiting for packets" in line:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Gateway ready\n")

                # Zeige Fehler und Warnungen immer an
                if any(keyword in line.lower() for keyword in ['error', 'fail', 'warning', 'invalid', 'usage:']):
                    print(f"⚠️  {line}")

                self.parse_line(line)

            # Warte auf Prozessende und zeige Exit-Code
            exit_code = process.wait()
            if exit_code != 0:
                print(f"\n⚠️  Process exited with code {exit_code}")
                if line_count == 0:
                    print("   No output received - possible parameter error")
                    print("\n   Try running manually on Dragino:")
                    print(f"   ssh root@{DRAGINO_HOST}")
                    print(f"   test_loragw_hal_rx -r {RADIO_TYPE} -a {FREQ_A} -b {FREQ_B} -k {CLOCK_SOURCE} -m {CHANNEL_MODE}")

        except KeyboardInterrupt:
            print("\n\n⏹️  Monitor stopped by user")
            process.terminate()

        except Exception as e:
            print(f"\n❌ Error: {e}")
            sys.exit(1)

        finally:
            print(f"\n📊 Total packets received: {self.packet_count}")
            if self.mqtt_client:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()


def main():
    # Declare globals before using them
    global MQTT_BROKER, MQTT_TOPIC

    parser = argparse.ArgumentParser(
        description="Remote LoRa packet monitor for Dragino Gateway (E22 Default Config)"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s v{VERSION}"
    )
    parser.add_argument(
        "--mqtt",
        action="store_true",
        help="Enable MQTT publishing to localhost:1883"
    )
    parser.add_argument(
        "--broker",
        default="localhost",
        help="MQTT broker address (default: localhost)"
    )
    parser.add_argument(
        "--topic",
        default=MQTT_TOPIC,
        help=f"MQTT topic (default: {MQTT_TOPIC})"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output (show all lines from Dragino)"
    )

    args = parser.parse_args()

    # Update globals mit CLI-Argumenten
    MQTT_BROKER = args.broker
    MQTT_TOPIC = args.topic

    # Starte Monitor
    monitor = DraginoMonitor(use_mqtt=args.mqtt)
    monitor.run(debug=args.debug)


if __name__ == "__main__":
    main()
