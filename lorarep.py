#!/usr/bin/python3
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
GATEWAY_ID = "48621185db7c38ca" # Deine ID aus der local_conf.json
FREQ_HZ = 868100000           # Die Frequenz deines E22 (z.B. 868.1 MHz)
DR = 5                        # Datenrate (SF7 für EU868)

# Topics (ChirpStack MQTT Forwarder Format)
TOPIC_UP = f"gateway/{GATEWAY_ID}/event/up"
TOPIC_DOWN = f"gateway/{GATEWAY_ID}/command/down"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info(f"Verbunden mit Broker (Code {rc})")
        client.subscribe(TOPIC_UP)
        logging.info(f"Abonniert: {TOPIC_UP}")
    else:
        logging.error(f"Verbindung fehlgeschlagen (Code {rc})")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload)

        # 1. Extrahiere die rohen LoRa-Daten (PhyPayload)
        # ChirpStack sendet diese als Base64
        raw_lora = data.get("phyPayload")

        if not raw_lora:
            logging.warning("Keine phyPayload in Nachricht gefunden")
            return

        # Safer access to rxInfo data
        rx_info_list = data.get('rxInfo', [])
        if not rx_info_list or not isinstance(rx_info_list, list) or len(rx_info_list) == 0:
            logging.warning("Keine rxInfo Daten verfügbar")
            rssi = "N/A"
            snr = "N/A"
        else:
            rx_info = rx_info_list[0]
            rssi = rx_info.get('rssi', 'N/A')
            snr = rx_info.get('snr', 'N/A')

        logging.info(f"--- Paket empfangen um {time.strftime('%H:%M:%S')} ---")
        logging.info(f"RSSI: {rssi} | SNR: {snr}")

        # 2. Baue den Sendeauftrag (Downlink)
        # Wir erzwingen die Frequenz, damit der E22 es hört!
        downlink = {
            "devEui": "0000000000000000", # Nicht relevant für Forwarder
            "confirmed": False,
            "fPort": 1,
            "data": raw_lora,             # Wir spiegeln die Payload 1:1
            "timing": {
                "immediately": {}         # Sofort senden
            },
            "txInfo": {
                "frequency": FREQ_HZ,     # <--- EXAKT DIE E22 FREQUENZ
                "power": 14,              # Sendeleistung in dBm
                "modulation": {
                    "lora": {
                        "bandwidth": 125000,
                        "spreadingFactor": 7,
                        "codeRate": "CR_4_5"
                    }
                }
            }
        }

        # 3. Zurückschicken über den WireGuard-Tunnel
        client.publish(TOPIC_DOWN, json.dumps(downlink))
        logging.info(f"Echo gesendet auf {FREQ_HZ/1000000} MHz")

    except json.JSONDecodeError as e:
        logging.error(f"JSON Decode Fehler: {e}")
    except Exception as e:
        logging.error(f"Fehler: {e}", exc_info=True)

def on_disconnect(client, userdata, rc):
    if rc != 0:
        logging.warning(f"Unerwartete Trennung vom Broker (Code {rc})")

# MQTT Client Setup
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

try:
    client.connect(BROKER, 1883, 60)
    logging.info("Starte MQTT Loop...")
    client.loop_forever()
except KeyboardInterrupt:
    logging.info("Beende durch Benutzer...")
    client.disconnect()
except Exception as e:
    logging.error(f"Kritischer Fehler: {e}", exc_info=True)
