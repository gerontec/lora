#!/usr/bin/python3
"""
Remote LoRa Packet Monitor für Dragino Gateway
Läuft auf heissa.de und verbindet sich via SSH zum Dragino

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

# --- KONFIGURATION ---
DRAGINO_HOST = "10.0.0.2"
DRAGINO_USER = "root"
FREQ_A = "867.1"
FREQ_B = "868.5"

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
            match = re.search(r'rssi_sig\s*:\s*([\d.]+)', line)
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

    def run(self):
        """Hauptloop: Verbindet zu Dragino und monitort Pakete"""
        print("=" * 60)
        print("Remote LoRa Packet Monitor")
        print("=" * 60)
        print(f"Dragino:   {DRAGINO_USER}@{DRAGINO_HOST}")
        print(f"Frequency: {FREQ_A} MHz and {FREQ_B} MHz")
        print(f"MQTT:      {'Enabled' if self.use_mqtt else 'Disabled'}")
        print("=" * 60)
        print()

        # Stoppe interferierende Services
        self.stop_dragino_services()

        # SSH Kommando
        cmd = [
            "ssh",
            f"{DRAGINO_USER}@{DRAGINO_HOST}",
            f"test_loragw_hal_rx -r 1250 -a {FREQ_A} -b {FREQ_B} -k 0"
        ]

        try:
            print(f"🔌 Connecting via SSH to {DRAGINO_HOST}...")

            # Starte SSH Prozess
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                universal_newlines=True
            )

            print("✅ Connected - monitoring packets...")
            print("   Press Ctrl+C to stop")
            print()

            # Lese Zeile für Zeile
            for line in process.stdout:
                line = line.strip()

                if "Waiting for packets" in line:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Gateway ready\n")

                self.parse_line(line)

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
    parser = argparse.ArgumentParser(
        description="Remote LoRa packet monitor for Dragino Gateway"
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

    args = parser.parse_args()

    # Update globals mit CLI-Argumenten
    global MQTT_BROKER, MQTT_TOPIC
    MQTT_BROKER = args.broker
    MQTT_TOPIC = args.topic

    # Starte Monitor
    monitor = DraginoMonitor(use_mqtt=args.mqtt)
    monitor.run()


if __name__ == "__main__":
    main()
