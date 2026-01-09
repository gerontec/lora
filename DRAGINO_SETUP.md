# Dragino Gateway Konfiguration für LoRa Repeater

Vollständige Anleitung zur Konfiguration des Dragino LPS8/DLOS8 Gateways für die Verwendung mit dem LoRa Repeater Service auf heissa.de.

## Netzwerk-Topologie

```
┌──────────────────┐    WireGuard VPN    ┌──────────────────┐
│  Dragino Gateway │◄──────────────────►│   heissa.de      │
│  10.0.0.2        │    Encrypted        │   10.0.0.1       │
│                  │    Tunnel           │   Kansas, USA    │
│  LoRa 868.1 MHz  │                     │                  │
│  MQTT Client     │                     │   Mosquitto      │
│  ChirpStack      │                     │   Port 1883      │
└──────────────────┘                     │   lorarep.py     │
                                         └──────────────────┘
```

## Voraussetzungen

- Dragino Gateway mit DLOS8 Firmware
- WireGuard VPN bereits konfiguriert und aktiv
- Zugriff auf heissa.de über WireGuard (10.0.0.1)
- Gateway-ID aus `/etc/lora/local_conf.json`

## Gateway-ID ermitteln

```bash
# Auf dem Dragino
cat /etc/lora/local_conf.json | grep gateway_ID
# Beispiel-Ausgabe: "gateway_ID": "48621185DB7C38CA"
```

**Wichtig:** ChirpStack nutzt die Gateway-ID in **Kleinbuchstaben**!
- Config hat: `48621185DB7C38CA`
- ChirpStack nutzt: `48621185db7c38ca`

## Option 1: ChirpStack MQTT Forwarder (Empfohlen für Standard-Setup)

### 1.1 ChirpStack MQTT Forwarder Konfiguration

**Datei:** `/etc/chirpstack-mqtt-forwarder/chirpstack-mqtt-forwarder.toml`

```toml
# Logging
[logging]
  level="info"
  log_to_syslog=true

# Backend (UDP von Packet Forwarder)
[backend]
  enabled="semtech_udp"

  [backend.semtech_udp]
    bind="0.0.0.0:1700"

# MQTT Integration
[mqtt]
  topic_prefix=""                        # WICHTIG: Leer lassen!
  server="tcp://10.0.0.1:1883"          # heissa.de WireGuard IP
  username=""
  password=""
  json=true                              # JSON statt Protobuf
  qos=0
  clean_session=true
```

**Konfiguration anpassen:**

```bash
# Backup erstellen
cp /etc/chirpstack-mqtt-forwarder/chirpstack-mqtt-forwarder.toml \
   /root/chirpstack-mqtt-forwarder.toml.backup

# topic_prefix leeren und server auf 10.0.0.1 setzen
sed -i 's/topic_prefix="eu868"/topic_prefix=""/' \
   /etc/chirpstack-mqtt-forwarder/chirpstack-mqtt-forwarder.toml
sed -i 's|server="tcp://heissa.de:1883"|server="tcp://10.0.0.1:1883"|' \
   /etc/chirpstack-mqtt-forwarder/chirpstack-mqtt-forwarder.toml

# Prüfen
grep -E "topic_prefix|server" /etc/chirpstack-mqtt-forwarder/chirpstack-mqtt-forwarder.toml
```

**Erwartete Ausgabe:**
```toml
  topic_prefix=""
  server="tcp://10.0.0.1:1883"
```

### 1.2 ChirpStack Service neu starten

```bash
# Hard restart
killall chirpstack-mqtt-forwarder
sleep 2
/etc/init.d/chirpstack-mqtt-forwarder start

# Status prüfen
ps | grep chirpstack
logread | grep chirpstack | tail -10
```

**Erwartete Logs:**
```
chirpstack-mqtt-forwarder: Starting ChirpStack MQTT Forwarder (version: 4.3.0)
chirpstack-mqtt-forwarder: Setting up Semtech UDP Packet Forwarder backend
chirpstack-mqtt-forwarder: Binding UDP socket, bind: 0.0.0.0:1700
chirpstack-mqtt-forwarder: Connecting to MQTT broker
chirpstack-mqtt-forwarder: Connected to MQTT broker
```

### 1.3 MQTT Topics

**ChirpStack sendet (Uplink vom Gateway):**
```
gateway/48621185db7c38ca/event/up
```

**ChirpStack empfängt (Downlink zum Gateway):**
```
gateway/48621185db7c38ca/command/down
```

## Option 2: Direktes MQTT (Alternative ohne ChirpStack)

Falls ChirpStack Probleme macht, kann man auch direkt MQTT nutzen.

### 2.1 MQTT Broker Konfiguration (UCI)

```bash
# MQTT Server auf heissa.de setzen
uci set mqtt.General.url='10.0.0.1'
uci set mqtt.General.port='1883'

# Client ID (Hostname des Dragino)
uci set mqtt.General.cid='dragino-27e318'

# Publish Topic (Dragino → heissa.de Uplink)
uci set mqtt.General.pub_topic='dragino-27e318/gateway1/data'

# Subscribe Topic (heissa.de → Dragino Downlink)
uci set mqtt.General.sub_topic='dragino-27e318/#'

# Optional: Credentials entfernen
uci set mqtt.General.user=''
uci set mqtt.General.pwd=''

# Speichern und anwenden
uci commit mqtt

# Service neu starten
/etc/init.d/iot-http restart

# Prüfen
uci show mqtt.General | grep -E "url|pub_topic|sub_topic|cid"
```

**Erwartete Ausgabe:**
```
mqtt.General.url='10.0.0.1'
mqtt.General.cid='dragino-27e318'
mqtt.General.pub_topic='dragino-27e318/gateway1/data'
mqtt.General.sub_topic='dragino-27e318/#'
```

### 2.2 MQTT Topics (Direktes Format)

**Dragino sendet (Uplink):**
```
dragino-27e318/gateway1/data
```

**Dragino empfängt (Downlink):**
```
dragino-27e318/gateway1/cmd
```

## heissa.de Konfiguration

### lorarep.py Topic Format

**Für ChirpStack (Option 1):**
```python
TOPIC_FORMAT = "chirpstack"
GATEWAY_ID = "48621185DB7C38CA"  # Uppercase in Config, lowercase in Topics!
```

**Für direktes MQTT (Option 2):**
```python
TOPIC_FORMAT = "dragino"
CLIENT_ID = "dragino-27e318"
CHANNEL_ID = "gateway1"
```

### Service neu starten

```bash
cd /home/gh/python/lora
git pull origin claude/configure-mqtt-dragino-3z1ZY
sudo systemctl restart lorarep.service
sudo systemctl status lorarep.service
```

## Testing und Verifikation

### Test 1: MQTT-Verbindung prüfen

**Auf dem Dragino:**
```bash
# Teste Verbindung zu heissa.de
ping -c 3 10.0.0.1

# Prüfe MQTT-Verbindung
netstat -tn | grep 10.0.0.1:1883

# Sollte zeigen:
# tcp ... 10.0.0.2:XXXXX 10.0.0.1:1883 ESTABLISHED
```

**Auf heissa.de:**
```bash
# Prüfe eingehende Verbindungen
sudo netstat -tnp | grep mosquitto | grep 10.0.0.2
```

### Test 2: MQTT Message Flow

**Terminal 1 (heissa.de) - MQTT Traffic überwachen:**
```bash
# Für ChirpStack
mosquitto_sub -h localhost -t "gateway/#" -v

# Für direktes MQTT
mosquitto_sub -h localhost -t "dragino-27e318/#" -v
```

**Terminal 2 (heissa.de) - lorarep.py Logs:**
```bash
sudo journalctl -u lorarep.service -f
```

**Terminal 3 (Dragino) - Test-Nachricht senden:**
```bash
# Für ChirpStack
mosquitto_pub -h 10.0.0.1 -t "gateway/48621185db7c38ca/event/up" \
  -m '{"phyPayload":"VGVzdA==","rxInfo":[{"rssi":-85,"snr":7.5}]}'

# Für direktes MQTT
mosquitto_pub -h 10.0.0.1 -t "dragino-27e318/gateway1/data" \
  -m '{"data":"VGVzdA==","rssi":-85,"snr":7.5}'
```

**Erwartete Reaktion auf heissa.de:**
- Terminal 1: Zeigt empfangene Uplink-Nachricht
- Terminal 1: Zeigt gesendete Downlink-Nachricht (Echo)
- Terminal 2: lorarep.py zeigt Paket-Verarbeitung

### Test 3: Downlink zum Gateway

**Auf heissa.de senden:**

**ChirpStack Format:**
```bash
mosquitto_pub -h localhost -t "gateway/48621185db7c38ca/command/down" -m '{
  "devEui": "0000000000000000",
  "confirmed": false,
  "fPort": 1,
  "data": "VGVzdA==",
  "timing": {"immediately": {}},
  "txInfo": {
    "frequency": 868100000,
    "power": 14,
    "modulation": {
      "lora": {
        "bandwidth": 125000,
        "spreadingFactor": 7,
        "codeRate": "CR_4_5"
      }
    }
  }
}'
```

**Direktes MQTT Format:**
```bash
mosquitto_pub -h localhost -t "dragino-27e318/gateway1/cmd" -m '{
  "data": "VGVzdA==",
  "frequency": 868100000,
  "datarate": "SF7BW125",
  "power": 14
}'
```

**Auf dem Dragino prüfen:**
```bash
# Logs überwachen
logread -f | grep -E "chirpstack|mqtt|downlink"

# Für ChirpStack erwartete Ausgabe:
# chirpstack-mqtt-forwarder: Received downlink command
# chirpstack-mqtt-forwarder: Sending downlink frame
```

### Test 4: End-to-End mit LoRa

Wenn ein E22 oder E90-DTU als Empfänger läuft:

1. E22/E90 auf 868.1 MHz konfigurieren
2. Test-Nachricht senden (siehe Test 3)
3. E22/E90 sollte LoRa-Paket empfangen

## Troubleshooting

### Problem: ChirpStack verbindet nicht mit MQTT

**Symptom:**
```bash
logread | grep chirpstack
# Zeigt nur: "Setting up Semtech UDP..."
# Zeigt NICHT: "Connected to MQTT"
```

**Lösung:**
```bash
# 1. Prüfe Config
cat /etc/chirpstack-mqtt-forwarder/chirpstack-mqtt-forwarder.toml

# 2. Stelle sicher:
#    - topic_prefix=""  (LEER!)
#    - server="tcp://10.0.0.1:1883"  (IP, nicht hostname!)

# 3. Hard restart
killall chirpstack-mqtt-forwarder
sleep 2
/etc/init.d/chirpstack-mqtt-forwarder start

# 4. Alternative: Nutze direktes MQTT (Option 2)
```

### Problem: MQTT Nachrichten kommen nicht an

**Auf dem Dragino testen:**
```bash
# Subscribe direkt auf MQTT
mosquitto_sub -h 10.0.0.1 -t "#" -v

# Dann auf heissa.de senden:
mosquitto_pub -h localhost -t "test" -m "hello"

# Wenn nichts ankommt:
# - WireGuard prüfen: wg show
# - Firewall prüfen: iptables -L
# - Mosquitto auf heissa.de: sudo systemctl status mosquitto
```

### Problem: Gateway-ID Groß-/Kleinschreibung

ChirpStack nutzt **lowercase** Gateway-IDs in Topics:
- Config: `48621185DB7C38CA`
- Topics: `48621185db7c38ca`

**Auf heissa.de beide Varianten testen:**
```bash
mosquitto_sub -h localhost -t "gateway/48621185DB7C38CA/#" -v &
mosquitto_sub -h localhost -t "gateway/48621185db7c38ca/#" -v &
```

### Problem: topic_prefix="eu868" noch gesetzt

**Symptom:** ChirpStack sendet auf `eu868/gateway/...` statt `gateway/...`

**Fix:**
```bash
sed -i 's/topic_prefix="eu868"/topic_prefix=""/' \
  /etc/chirpstack-mqtt-forwarder/chirpstack-mqtt-forwarder.toml
killall chirpstack-mqtt-forwarder
/etc/init.d/chirpstack-mqtt-forwarder start
```

## Performance-Tipps

### Log-Level reduzieren

Wenn alles funktioniert, Log-Level auf "warn" setzen:

```toml
[logging]
  level="warn"
  log_to_syslog=true
```

### MQTT QoS

Für minimale Latenz QoS 0 nutzen (best effort):

```toml
[mqtt]
  qos=0
```

## Monitoring

### MQTT Traffic auf heissa.de

```bash
# Alle Topics anzeigen
mosquitto_sub -h localhost -t "#" -v | grep dragino

# Nur Uplinks
mosquitto_sub -h localhost -t "gateway/+/event/up" -v

# Nur Downlinks
mosquitto_sub -h localhost -t "gateway/+/command/down" -v
```

### ChirpStack Statistiken

```bash
# Auf dem Dragino
logread | grep chirpstack | grep -E "uplink|downlink" | tail -20
```

## Weitere Informationen

- **LoRa Repeater Service:** [LORAREP_SERVICE.md](LORAREP_SERVICE.md)
- **System Dokumentation:** [README_SYSTEM.md](README_SYSTEM.md)
- **ChirpStack MQTT Forwarder:** https://www.chirpstack.io/docs/chirpstack-mqtt-forwarder/
