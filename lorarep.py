#!/usr/bin/python3
"""
LoRa Repeater Service mit flexiblem MQTT-Format Support

Unterstützt:
  - Dragino MQTT Format (einfach, direkt)
  - ChirpStack MQTT Forwarder Format (komplex, standardisiert)

Konfiguration:
  1. Setze TOPIC_FORMAT = "dragino" oder "chirpstack"
  2. Für Dragino: Konfiguriere CLIENT_ID und CHANNEL_ID
  3. Für ChirpStack: Konfiguriere GATEWAY_ID
  4. Passe FREQ_HZ an deine E22-Frequenz an

Dragino Topic Struktur:
  Subscribe: CLIENTID/#
  Publish:   CLIENTID/CHANNEL/cmd

ChirpStack Topic Struktur:
  Subscribe: gateway/GATEWAY_ID/event/up
  Publish:   gateway/GATEWAY_ID/command/down
"""
import paho.mqtt.client as mqtt
import json
import base64
import time
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# --- KONFIGURATION ---
BROKER = "127.0.0.1"          # Da das Skript auf heissa.de läuft
GATEWAY_ID = "48621185DB7C38CA" # Local ID aus der local_conf.json
FREQ_HZ = 868100000           # Die Frequenz deines E22 (z.B. 868.1 MHz)
DR = 5                        # Datenrate (SF7 für EU868)

# Topic Format Selection
# Optionen: "chirpstack" oder "dragino"
TOPIC_FORMAT = "dragino"

# Client und Channel IDs für Dragino Format
CLIENT_ID = "dragino-27e318"  # Dragino Client ID (aus Hostname)
CHANNEL_ID = "gateway1"       # Dein Channel

# Topics werden basierend auf Format gesetzt
if TOPIC_FORMAT == "dragino":
    TOPIC_UP = f"{CLIENT_ID}/{CHANNEL_ID}/data"
    TOPIC_DOWN = f"{CLIENT_ID}/{CHANNEL_ID}/cmd"
    TOPIC_SUB = f"{CLIENT_ID}/+/data"  # Subscribe only to data topics (avoid feedback loop)
else:  # chirpstack
    TOPIC_UP = f"gateway/{GATEWAY_ID}/event/up"
    TOPIC_DOWN = f"gateway/{GATEWAY_ID}/command/down"
    TOPIC_SUB = TOPIC_UP

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        logging.info(f"Verbunden mit Broker (Code {reason_code})")
        logging.info(f"Topic Format: {TOPIC_FORMAT}")
        client.subscribe(TOPIC_SUB)
        logging.info(f"Abonniert: {TOPIC_SUB}")
    else:
        logging.error(f"Verbindung fehlgeschlagen (Code {reason_code})")

def parse_message(data, msg_topic):
    """Extrahiert LoRa-Daten aus verschiedenen MQTT-Formaten"""
    raw_lora = None
    rssi = "N/A"
    snr = "N/A"

    if TOPIC_FORMAT == "dragino":
        # Dragino Format: Einfachere Struktur
        # Prüfe verschiedene mögliche Payload-Felder
        raw_lora = data.get("data") or data.get("payload") or data.get("phyPayload")

        # RSSI/SNR können direkt im data oder in rxInfo sein
        rssi = data.get("rssi", "N/A")
        snr = data.get("snr", "N/A")

        # Fallback zu rxInfo wenn vorhanden
        if rssi == "N/A" and "rxInfo" in data:
            rx_info = data["rxInfo"]
            if isinstance(rx_info, list) and len(rx_info) > 0:
                rssi = rx_info[0].get("rssi", "N/A")
                snr = rx_info[0].get("snr", "N/A")
    else:
        # ChirpStack Format
        raw_lora = data.get("phyPayload")

        rx_info_list = data.get('rxInfo', [])
        if rx_info_list and isinstance(rx_info_list, list) and len(rx_info_list) > 0:
            rx_info = rx_info_list[0]
            rssi = rx_info.get('rssi', 'N/A')
            snr = rx_info.get('snr', 'N/A')

    return raw_lora, rssi, snr

def build_downlink(raw_lora):
    """Erstellt Downlink-Nachricht im passenden Format"""
    if TOPIC_FORMAT == "dragino":
        # Dragino Format: Vereinfacht
        downlink = {
            "data": raw_lora,
            "frequency": FREQ_HZ,
            "datarate": f"SF{7}BW125",  # SF7, BW125kHz
            "power": 14
        }
    else:
        # ChirpStack Format
        downlink = {
            "devEui": "0000000000000000",
            "confirmed": False,
            "fPort": 1,
            "data": raw_lora,
            "timing": {
                "immediately": {}
            },
            "txInfo": {
                "frequency": FREQ_HZ,
                "power": 14,
                "modulation": {
                    "lora": {
                        "bandwidth": 125000,
                        "spreadingFactor": 7,
                        "codeRate": "CR_4_5"
                    }
                }
            }
        }
    return downlink

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload)

        # Parse Message basierend auf Format
        raw_lora, rssi, snr = parse_message(data, msg.topic)

        if not raw_lora:
            logging.warning(f"Keine Payload in Nachricht gefunden (Topic: {msg.topic})")
            return

        logging.info(f"--- Paket empfangen um {time.strftime('%H:%M:%S')} ---")
        logging.info(f"Topic: {msg.topic}")
        logging.info(f"RSSI: {rssi} | SNR: {snr}")

        # Baue Downlink basierend auf Format
        downlink = build_downlink(raw_lora)

        # Zurückschicken
        client.publish(TOPIC_DOWN, json.dumps(downlink))
        logging.info(f"Echo gesendet auf {FREQ_HZ/1000000} MHz (Format: {TOPIC_FORMAT})")

    except json.JSONDecodeError as e:
        logging.error(f"JSON Decode Fehler: {e}")
        logging.error(f"Payload: {msg.payload[:200]}")  # Erste 200 Bytes anzeigen
    except Exception as e:
        logging.error(f"Fehler: {e}", exc_info=True)

def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    if reason_code != 0:
        logging.warning(f"Unerwartete Trennung vom Broker (Code {reason_code})")

# MQTT Client Setup
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

try:
    logging.info("=" * 60)
    logging.info("LoRa Repeater Service startet...")
    logging.info("=" * 60)
    logging.info(f"Konfiguration:")
    logging.info(f"  MQTT Broker:    {BROKER}:1883")
    logging.info(f"  Topic Format:   {TOPIC_FORMAT}")
    if TOPIC_FORMAT == "dragino":
        logging.info(f"  Client ID:      {CLIENT_ID}")
        logging.info(f"  Channel ID:     {CHANNEL_ID}")
        logging.info(f"  Subscribe:      {TOPIC_SUB}")
        logging.info(f"  Publish (Down): {TOPIC_DOWN}")
    else:
        logging.info(f"  Gateway ID:     {GATEWAY_ID}")
        logging.info(f"  Subscribe:      {TOPIC_SUB}")
        logging.info(f"  Publish (Down): {TOPIC_DOWN}")
    logging.info(f"  Frequenz:       {FREQ_HZ/1000000} MHz")
    logging.info(f"  Spreading Factor: SF7")
    logging.info(f"  Sendeleistung:  14 dBm")
    logging.info("=" * 60)

    client.connect(BROKER, 1883, 60)
    logging.info("Starte MQTT Loop...")
    client.loop_forever()
except KeyboardInterrupt:
    logging.info("\nBeende durch Benutzer...")
    client.disconnect()
except Exception as e:
    logging.error(f"Kritischer Fehler: {e}", exc_info=True)
