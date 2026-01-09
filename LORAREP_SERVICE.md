# LoRa Repeater Service auf heissa.de

Dokumentation für den systemd Service, der `lorarep.py` als Daemon auf heissa.de ausführt.

## Systemd Service Konfiguration

### Service-Datei: `/etc/systemd/system/lorarep.service`

```ini
[Unit]
Description=LoRaWAN WireGuard Repeater Mirror
After=network.target mosquitto.service
Wants=network-online.target

[Service]
Type=simple
User=gh
Group=gh
WorkingDirectory=/home/gh/python/lora
ExecStart=/usr/bin/python3 /home/gh/python/lora/lorarep.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Sicherheitseinstellungen
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

## Installation

### 1. Service-Datei erstellen

```bash
sudo nano /etc/systemd/system/lorarep.service
# Füge obige Konfiguration ein
```

### 2. Service aktivieren und starten

```bash
# Systemd neu laden
sudo systemctl daemon-reload

# Service aktivieren (Autostart beim Booten)
sudo systemctl enable lorarep.service

# Service starten
sudo systemctl start lorarep.service

# Status prüfen
sudo systemctl status lorarep.service
```

## Service Management

### Grundlegende Befehle

```bash
# Service starten
sudo systemctl start lorarep.service

# Service stoppen
sudo systemctl stop lorarep.service

# Service neu starten
sudo systemctl restart lorarep.service

# Service Status anzeigen
sudo systemctl status lorarep.service

# Service deaktivieren (kein Autostart)
sudo systemctl disable lorarep.service
```

### Nach Code-Updates

```bash
# Neueste Änderungen pullen und Service neu starten
cd /home/gh/python/lora
git pull origin claude/configure-mqtt-dragino-3z1ZY
sudo systemctl restart lorarep.service
sudo systemctl status lorarep.service
```

## Logs überwachen

### Live Logs anzeigen

```bash
# Alle Logs in Echtzeit
sudo journalctl -u lorarep.service -f

# Letzte 50 Zeilen
sudo journalctl -u lorarep.service -n 50

# Logs der letzten Stunde
sudo journalctl -u lorarep.service --since "1 hour ago"

# Logs von heute
sudo journalctl -u lorarep.service --since today

# Mit Zeitstempel
sudo journalctl -u lorarep.service -o short-precise -f
```

### Erwartete Log-Ausgabe

**Beim Start (Dragino-Format):**
```
Jan 09 10:21:35 heissa python3[4187570]: 2026-01-09 10:21:35 - INFO - ============================================================
Jan 09 10:21:35 heissa python3[4187570]: 2026-01-09 10:21:35 - INFO - LoRa Repeater Service startet...
Jan 09 10:21:35 heissa python3[4187570]: 2026-01-09 10:21:35 - INFO - ============================================================
Jan 09 10:21:35 heissa python3[4187570]: 2026-01-09 10:21:35 - INFO - Konfiguration:
Jan 09 10:21:35 heissa python3[4187570]: 2026-01-09 10:21:35 - INFO -   MQTT Broker:    127.0.0.1:1883
Jan 09 10:21:35 heissa python3[4187570]: 2026-01-09 10:21:35 - INFO -   Topic Format:   dragino
Jan 09 10:21:35 heissa python3[4187570]: 2026-01-09 10:21:35 - INFO -   Client ID:      dragino-27e318
Jan 09 10:21:35 heissa python3[4187570]: 2026-01-09 10:21:35 - INFO -   Channel ID:     gateway1
Jan 09 10:21:35 heissa python3[4187570]: 2026-01-09 10:21:35 - INFO -   Subscribe:      dragino-27e318/#
Jan 09 10:21:35 heissa python3[4187570]: 2026-01-09 10:21:35 - INFO -   Publish (Down): dragino-27e318/gateway1/cmd
Jan 09 10:21:35 heissa python3[4187570]: 2026-01-09 10:21:35 - INFO -   Frequenz:       868.1 MHz
Jan 09 10:21:35 heissa python3[4187570]: 2026-01-09 10:21:35 - INFO - Starte MQTT Loop...
Jan 09 10:21:35 heissa python3[4187570]: 2026-01-09 10:21:35 - INFO - Verbunden mit Broker (Code Success)
Jan 09 10:21:35 heissa python3[4187570]: 2026-01-09 10:21:35 - INFO - Topic Format: dragino
Jan 09 10:21:35 heissa python3[4187570]: 2026-01-09 10:21:35 - INFO - Abonniert: dragino-27e318/#
```

**Bei Paket-Empfang:**
```
Jan 09 10:25:42 heissa python3[4187570]: 2026-01-09 10:25:42 - INFO - --- Paket empfangen um 10:25:42 ---
Jan 09 10:25:42 heissa python3[4187570]: 2026-01-09 10:25:42 - INFO - Topic: dragino-27e318/gateway1/data
Jan 09 10:25:42 heissa python3[4187570]: 2026-01-09 10:25:42 - INFO - RSSI: -85 | SNR: 7.5
Jan 09 10:25:42 heissa python3[4187570]: 2026-01-09 10:25:42 - INFO - Echo gesendet auf 868.1 MHz (Format: dragino)
```

## MQTT Test-Nachrichten

### Test-Nachricht senden (Dragino-Format)

```bash
# Einfacher Test
mosquitto_pub -h localhost -t "dragino-27e318/gateway1/data" -m '{
  "data": "VGVzdA==",
  "rssi": -85,
  "snr": 7.5
}'

# Mit vollständigen Metadaten
mosquitto_pub -h localhost -t "dragino-27e318/gateway1/data" -m '{
  "data": "SGVsbG8gTG9SYQ==",
  "rssi": -90,
  "snr": 6.2,
  "frequency": 868100000
}'
```

**Base64-Payloads:**
- `VGVzdA==` → "Test"
- `SGVsbG8gTG9SYQ==` → "Hello LoRa"
- `AQIDBA==` → 0x01 0x02 0x03 0x04

### MQTT Topics überwachen

```bash
# Alle Topics anzeigen
mosquitto_sub -h localhost -t "#" -v

# Nur Dragino Topics
mosquitto_sub -h localhost -t "dragino-27e318/#" -v

# Nur Uplink (vom Gateway)
mosquitto_sub -h localhost -t "dragino-27e318/+/data" -v

# Nur Downlink (zum Gateway)
mosquitto_sub -h localhost -t "dragino-27e318/+/cmd" -v
```

## Troubleshooting

### Service startet nicht

```bash
# Detaillierte Fehlermeldungen
sudo systemctl status lorarep.service -l

# Prüfe Python-Syntax
python3 -m py_compile /home/gh/python/lora/lorarep.py

# Prüfe Abhängigkeiten
python3 -c "import paho.mqtt.client as mqtt; print('OK')"

# Manuelle Ausführung zum Debugging
cd /home/gh/python/lora
python3 lorarep.py
```

### MQTT Broker läuft nicht

```bash
# Mosquitto Status prüfen
sudo systemctl status mosquitto

# Mosquitto starten
sudo systemctl start mosquitto

# Mosquitto Port testen
netstat -tuln | grep 1883
```

### Service läuft, aber keine Pakete werden empfangen

```bash
# 1. Prüfe aktive Topics
mosquitto_sub -h localhost -t "#" -v

# 2. Prüfe Service-Logs
sudo journalctl -u lorarep.service -n 100

# 3. Sende Test-Nachricht
mosquitto_pub -h localhost -t "dragino-27e318/gateway1/data" -m '{"data":"VGVzdA=="}'

# 4. Prüfe MQTT Verbindung
sudo netstat -tnp | grep python3
```

### Konfiguration prüfen

```bash
# Zeige aktive Konfiguration
grep "TOPIC_FORMAT\|CLIENT_ID\|GATEWAY_ID" /home/gh/python/lora/lorarep.py
```

## Performance und Monitoring

### Ressourcen-Verbrauch prüfen

```bash
# CPU und Memory
systemctl status lorarep.service

# Detaillierte Statistiken
systemd-cgtop -m

# Prozess-Informationen
ps aux | grep lorarep.py
```

### Service-Statistiken

```bash
# Service Uptime und Restart-Count
systemctl show lorarep.service | grep -E 'ExecMainStartTimestamp|NRestarts'

# Letzte Starts/Stops
sudo journalctl -u lorarep.service | grep -E 'Started|Stopped'
```

## Wartung

### Service-Update Prozedur

```bash
# 1. Aktuelle Version sichern
cd /home/gh/python/lora
git status

# 2. Neueste Änderungen pullen
git fetch origin
git checkout claude/configure-mqtt-dragino-3z1ZY
git pull

# 3. Syntax-Check
python3 -m py_compile lorarep.py

# 4. Service neu starten
sudo systemctl restart lorarep.service

# 5. Logs überwachen (erste 30 Sekunden)
sudo journalctl -u lorarep.service -f
```

### Log-Rotation

Systemd journald rotiert Logs automatisch. Konfiguration in `/etc/systemd/journald.conf`:

```ini
[Journal]
SystemMaxUse=500M
SystemMaxFileSize=50M
RuntimeMaxUse=100M
```

### Backup

```bash
# Service-Datei sichern
sudo cp /etc/systemd/system/lorarep.service /root/backup/

# Skript sichern
cp /home/gh/python/lora/lorarep.py /home/gh/backup/
```

## Sicherheit

### Service-Benutzer

Der Service läuft als User `gh` (nicht root) für bessere Sicherheit.

### Berechtigungen prüfen

```bash
# Datei-Berechtigungen
ls -la /home/gh/python/lora/lorarep.py
# Sollte: -rwxr-xr-x gh gh

# Service-Datei Berechtigungen
ls -la /etc/systemd/system/lorarep.service
# Sollte: -rw-r--r-- root root
```

## Netzwerk-Architektur

```
┌──────────────────┐           ┌──────────────────┐
│  Dragino Gateway │           │   heissa.de      │
│  (10.0.0.1)      │ ◄─WG──────┤   (Kansas, USA)  │
│                  │           │                  │
│  LoRa 868.1 MHz  │           │  Mosquitto       │
│  MQTT Client     │           │  Port 1883       │
│                  │           │                  │
│  Publish:        │           │  lorarep.service │
│  dragino-27e318/ │  ────────►│  Subscribe:      │
│  gateway1/data   │           │  dragino-27e318/#│
│                  │           │                  │
│  Subscribe:      │  ◄────────│  Publish:        │
│  dragino-27e318/#│           │  dragino-27e318/ │
│                  │           │  gateway1/cmd    │
└──────────────────┘           └──────────────────┘
```

## Weitere Informationen

- **Hauptdokumentation:** [README_SYSTEM.md](README_SYSTEM.md)
- **Deployment Guide:** [REPEATER_DEPLOYMENT.md](REPEATER_DEPLOYMENT.md)
- **Changelog:** [CHANGELOG.md](CHANGELOG.md)
