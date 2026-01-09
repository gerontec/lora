# LoRa Repeater System Dokumentation

## Systemübersicht

Dieses System implementiert einen LoRa-Repeater über einen WireGuard-Tunnel, der LoRa-Pakete zwischen einem lokalen E22-Modul und einem entfernten Dragino-Gateway spiegelt.

```
┌─────────────────┐                    ┌──────────────────┐                    ┌─────────────────┐
│  Ebyte E22 USB  │ ───LoRa 868MHz───> │ Dragino Gateway  │ ───WireGuard───>  │  heissa.de      │
│  Sender/Empf.   │ <──LoRa 868MHz──── │   (10.0.0.1)     │ <──WireGuard────  │  (Kansas, USA)  │
└─────────────────┘                    └──────────────────┘                    └─────────────────┘
                                              │                                        │
                                              │ UDP Port 1700                          │ MQTT
                                              │ (Semtech Protocol)                     │ Port 1883
                                              └────────────────────────────────────────┘
                                                    RTT: ~260ms (130ms + 130ms)
```

## Hardware-Komponenten

### 1. Ebyte E22 LoRa-Modul (USB)
- **Frequenz**: 868.1 MHz (868100000 Hz)
- **Air Rate**: Konfigurierbar (0.3k - 62.5k)
- **Transmit Power**: 13-27 dBm
- **Schnittstelle**: USB Serial (/dev/ttyUSB0)
- **Baudrate**: 9600 (Standard)

### 2. Dragino LoRaWAN Gateway
- **Gateway ID**: `48621185db7c38ca`
- **Plattform**: SX1302
- **Standort**: 47.679°N, 11.579°E, 680m (Alpenregion)
- **IP-Adresse (WireGuard)**: 10.0.0.1
- **Region**: EU868
- **Beacon Frequenz**: 869.525 MHz

### 3. Server (heissa.de)
- **Standort**: Kansas, USA
- **Latenz zum Gateway**: ~130ms (one-way)
- **Dienste**:
  - MQTT Broker (Mosquitto, Port 1883)
  - ChirpStack MQTT Forwarder
  - LoRa Repeater Daemon (lorarep.py)

## Netzwerk-Topologie

### WireGuard VPN Tunnel
- **Gateway**: 10.0.0.1 (Dragino)
- **Server**: 10.0.0.2 (heissa.de, angenommen)
- **Round-Trip Time (RTT)**: ~260ms
- **Tunnel**: Dragino ↔ heissa.de

### Dragino Gateway Konfiguration

**Server 1 (The Things Network)** - Deaktiviert
```json
{
  "server_name": "server",
  "enable": "false",
  "server_address": "eu1.cloud.thethings.network",
  "serv_port_up": 1700,
  "serv_port_down": 1700
}
```

**Server 2 (Lokaler MQTT Server)** - Aktiv
```json
{
  "server_name": "server2",
  "server_address": "192.168.178.23",
  "serv_port_up": 1700,
  "serv_port_down": 1700
}
```

## Software-Komponenten

### 1. E22 Konfigurationsskripte

#### e22.py
Hauptkonfigurationsskript für das E22-Modul mit folgenden Funktionen:
- Lesen/Schreiben der Modulkonfiguration
- RSSI-Messung (Bit 5 in REG1)
- Ambient Noise RSSI (Bit 7 in REG3)
- Verschlüsselungsschlüssel setzen
- Produkt-Informationen auslesen

**Wichtige Parameter für Repeater-Betrieb:**
```bash
./e22.py --port /dev/ttyUSB0 \
  --channel 21 \
  --air-rate 2.4k \
  --baud-rate 9600 \
  --power 22dBm \
  --rssi-enable 1
```

**Frequenzberechnung:**
```
Frequenz = 850.125 MHz + Channel * 1 MHz
Channel 21 = 850.125 + 21 = 871.125 MHz
```
⚠️ **Hinweis**: Für 868.1 MHz sollte Channel 18 verwendet werden.

#### Weitere Hilfsskripte
- **e22_read.py**: Nur Konfiguration auslesen
- **e22_set.py**: Schnelle Konfiguration setzen
- **e22conf.py**: Erweiterte Konfiguration

### 2. LoRa Repeater Service (heissa.de)

#### lorarep.py
MQTT-basierter LoRa-Repeater-Daemon mit folgenden Features:

**Funktionsweise:**
1. Abonniert: `gateway/48621185db7c38ca/event/up`
2. Empfängt LoRa-Pakete vom Dragino Gateway
3. Extrahiert PhyPayload (Base64)
4. Spiegelt die Payload zurück als Downlink
5. Publiziert auf: `gateway/48621185db7c38ca/command/down`
6. Gateway sendet auf **exakt 868.1 MHz** zurück

**Downlink-Konfiguration:**
```python
{
    "frequency": 868100000,      # Exakt E22 Frequenz
    "power": 14,                 # dBm
    "modulation": {
        "lora": {
            "bandwidth": 125000,
            "spreadingFactor": 7,
            "codeRate": "CR_4_5"
        }
    }
}
```

**Systemd Service:**
```ini
[Unit]
Description=LoRaWAN WireGuard Repeater Mirror
After=network.target

[Service]
Type=simple
User=gh
WorkingDirectory=/home/gh/python/lora
ExecStart=/usr/bin/python3 /home/gh/python/lora/lorarep.py
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Service Management:**
```bash
# Service starten
sudo systemctl start lorarep.service

# Service Status prüfen
sudo systemctl status lorarep.service

# Logs anschauen
sudo journalctl -u lorarep.service -f

# Service bei Boot aktivieren
sudo systemctl enable lorarep.service
```

### 3. Weitere Python-Skripte

#### lorain.py
LoRa-Empfänger für direkte serielle Kommunikation:
- Empfängt UTF-8 und binäre LoRa-Nachrichten
- Sendet RSSI-Anfragen
- Loggt zu `/tmp/lorain.log`

#### sendtcp.py
TCP-basierter LoRa-Sender

## Datenfluss im Repeater-System

### Uplink (E22 → Gateway → heissa.de)
```
1. E22 sendet LoRa-Paket auf 868.1 MHz
   └─> Air Time: ~100-500ms (abhängig von SF)

2. Dragino Gateway empfängt Paket
   └─> Verarbeitung: ~10ms

3. Gateway sendet UDP an heissa.de (Semtech Protocol)
   └─> WireGuard Tunnel: ~130ms

4. MQTT Broker empfängt Paket
   └─> Topic: gateway/48621185db7c38ca/event/up
   └─> Verarbeitung: ~5ms

5. lorarep.py verarbeitet Nachricht
   └─> Parsing + Echo-Vorbereitung: ~10ms
```

### Downlink (heissa.de → Gateway → E22)
```
6. lorarep.py publiziert Downlink
   └─> Topic: gateway/48621185db7c38ca/command/down

7. ChirpStack Forwarder sendet UDP zurück
   └─> WireGuard Tunnel: ~130ms

8. Dragino Gateway empfängt Downlink
   └─> Scheduling: ~10ms

9. Gateway sendet auf 868.1 MHz
   └─> Air Time: ~100-500ms

10. E22 empfängt Echo
    └─> Total Round-Trip Time: ~400-800ms
```

## Systemleistung

### Latenz-Breakdown
| Komponente | Latenz |
|------------|--------|
| LoRa Air Time (SF7) | ~100-200ms |
| Gateway Processing | ~20ms |
| WireGuard (one-way) | ~130ms |
| MQTT + lorarep.py | ~15ms |
| **Total One-Way** | **~265-365ms** |
| **Total Round-Trip** | **~530-730ms** |

### Messwerte
- **Ping RTT (WireGuard)**: 126-129ms
- **Gateway → heissa.de**: ~130ms
- **heissa.de → Gateway**: ~130ms
- **Total System RTT**: ~400-800ms (inkl. LoRa Air Time)

## Frequenz-Konfiguration

### EU868 Frequenzen (Standard LoRaWAN)
| Kanal | Frequenz (MHz) | Verwendung |
|-------|---------------|-----------|
| 0 | 868.100 | Uplink |
| 1 | 868.300 | Uplink |
| 2 | 868.500 | Uplink |
| 3 | 867.100 | Uplink |
| 4 | 867.300 | Uplink |
| 5 | 867.500 | Uplink |
| 6 | 867.700 | Uplink |
| 7 | 867.900 | Uplink |
| - | 869.525 | RX2/Beacon |

### E22 Konfiguration für 868.1 MHz
```bash
# Kanal berechnen: (868.1 - 850.125) ≈ Channel 18
./e22.py --channel 18 --air-rate 2.4k --power 22dBm
```

## Fehlerbehandlung und Logging

### lorarep.py Logging
- **Level**: INFO (Standardbetrieb), DEBUG (Troubleshooting)
- **Format**: `YYYY-MM-DD HH:MM:SS - LEVEL - Message`
- **Ausgabe**: systemd journal

**Log-Beispiel:**
```
2026-01-09 05:30:49 - INFO - Starte MQTT Loop...
2026-01-09 05:30:49 - INFO - Verbunden mit Broker (Code 0)
2026-01-09 05:30:49 - INFO - Abonniert: gateway/48621185db7c38ca/event/up
2026-01-09 05:31:15 - INFO - --- Paket empfangen um 05:31:15 ---
2026-01-09 05:31:15 - INFO - RSSI: -85 | SNR: 8.5
2026-01-09 05:31:15 - INFO - Echo gesendet auf 868.1 MHz
```

### Häufige Probleme

**1. Keine MQTT Verbindung**
```bash
# Mosquitto Status prüfen
sudo systemctl status mosquitto

# Port prüfen
netstat -tlnp | grep 1883
```

**2. Gateway sendet nicht zurück**
- Downlink-Frequenz prüfen (muss exakt 868.1 MHz sein)
- Gateway-Logs prüfen: `logread -f`
- Duty Cycle beachten (EU868: 1% bei 868 MHz)

**3. E22 empfängt nicht**
- RSSI Enable aktivieren: `--rssi-enable 1`
- Richtige Frequenz/Kanal prüfen
- Air Rate muss übereinstimmen (Gateway SF7 ≈ E22 2.4k)

## Installation auf heissa.de

### Repository klonen
```bash
cd ~/python
git clone https://github.com/gerontec/lora.git
cd lora
git checkout claude/find-fix-bug-mk5rxnb39nbsdh8l-0MNU3
```

### Service einrichten
```bash
# Service-Datei kopieren/erstellen
sudo nano /etc/systemd/system/lorarep.service

# Daemon neu laden
sudo systemctl daemon-reload

# Service starten und aktivieren
sudo systemctl enable --now lorarep.service

# Status prüfen
sudo systemctl status lorarep.service
```

### Abhängigkeiten
```bash
# paho-mqtt installieren
pip3 install paho-mqtt

# oder mit apt (Debian/Ubuntu)
sudo apt install python3-paho-mqtt
```

## Sicherheit und Best Practices

### WireGuard-Sicherheit
- Nur notwendige Ports öffnen (UDP für WireGuard)
- Firewall-Regeln für 10.0.0.0/24 Netz
- Regelmäßige Key-Rotation

### MQTT-Sicherheit
- Aktuell: Unverschlüsselt auf localhost
- Empfohlen: TLS aktivieren für externe Verbindungen
- Authentifizierung aktivieren

### LoRa Best Practices
- Duty Cycle beachten (EU: max 1% bei 868 MHz)
- Angemessene Transmission Power (nicht immer Maximum)
- Air Time minimieren (SF7 bevorzugen wenn möglich)

## Testing und Debugging

### Test 1: MQTT Verbindung
```bash
# Subscribe auf Uplink
mosquitto_sub -h localhost -t "gateway/48621185db7c38ca/event/up" -v

# Subscribe auf Downlink
mosquitto_sub -h localhost -t "gateway/48621185db7c38ca/command/down" -v
```

### Test 2: E22 Modul
```bash
# Konfiguration auslesen
./e22.py --port /dev/ttyUSB0

# RSSI testen
./e22.py --port /dev/ttyUSB0 --rssi-enable 1
```

### Test 3: WireGuard Tunnel
```bash
# Ping von heissa.de zum Gateway
ping -c 5 10.0.0.1

# Traceroute
traceroute 10.0.0.1
```

### Test 4: End-to-End
```bash
# Auf E22 Seite: lorain.py starten (Empfänger)
python3 lorain.py

# Auf anderem Terminal: Nachricht senden
python3 sendtcp.py "Test Message"

# Logs auf heissa.de beobachten
sudo journalctl -u lorarep.service -f
```

## Changelog

### Version 1.2 (2026-01-09)
- ✅ Fix: paho-mqtt API v2 Migration (DeprecationWarning behoben)
- ✅ Aktualisierte Callback-Signaturen für `on_connect` und `on_disconnect`

### Version 1.1 (2026-01-09)
- ✅ Verbesserte Fehlerbehandlung in lorarep.py
- ✅ Sichere rxInfo-Zugriffe (keine Crashes bei fehlenden Daten)
- ✅ Strukturiertes Logging mit Timestamps
- ✅ Graceful Shutdown bei KeyboardInterrupt

### Version 1.0 (2026-01-08)
- ✅ Fix: Bug in e22.py (noise_enable überschrieb rssi_enable)
- ✅ Initiale lorarep.py Implementierung
- ✅ Systemd Service Integration

## Lizenz und Kontakt

**Maintainer**: gh@heissa.de
**Repository**: https://github.com/gerontec/lora
**Gateway Location**: 47.679°N, 11.579°E (Alpenregion)

## Referenzen

- [Ebyte E22 Datasheet](https://www.ebyte.com/en/product-view-news.html?id=1112)
- [Dragino Documentation](https://www.dragino.com/)
- [ChirpStack MQTT Forwarder](https://www.chirpstack.io/)
- [LoRaWAN Regional Parameters EU868](https://lora-alliance.org/resource_hub/rp2-1-0-3-lorawan-regional-parameters/)
- Research Paper: [2020_Höchstetal_LoRaDeviceSmartphoneCommunicationCrisisScenarios.pdf](2020_Höchstetal_LoRaDeviceSmartphoneCommunicationCrisisScenarios.pdf)
