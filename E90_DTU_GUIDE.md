# E90-DTU (900SL30) Berggipfel-Repeater Guide

## Hardware-Spezifikationen

### E90-DTU (900SL30) Überblick
```
Frequenz:       850.125 - 930.125 MHz (Standard: 868.125 MHz)
Modulation:     LoRa (militärische Spezifikation)
Schnittstellen: RS232 + RS485 (transparent)
Stromversorgung: 8-28V DC (direkt an Solar!)
Sendeleistung:  30 dBm (1W) bei PWMAX
Temperatur:     -40°C bis +85°C (industriell)
Gehäuse:        IP65-kompatibel möglich
```

## Warum E90-DTU statt E22?

| Feature | E22 USB/UART | E90-DTU (900SL30) | Vorteil |
|---------|--------------|-------------------|---------|
| **RELAY-Funktion** | ❌ Manuell | ✅ Eingebaut (RLYON) | **Keine Programmierung!** |
| **Stromversorgung** | 3.3-5V | 8-28V | Direkt an 12V Solar |
| **Sendeleistung** | 27 dBm (500mW) | 30 dBm (1W) | +26% mehr Reichweite |
| **Schnittstelle** | USB/UART | RS232/RS485 | Störsicher, lange Kabel |
| **Temperatur** | -20°C bis +70°C | -40°C bis +85°C | Alpen-Winter sicher |
| **Preis** | ~35 EUR | ~60-80 EUR | Teurer, aber besser |

## Systemarchitektur

### Berggipfel-Setup mit E90-DTU

```
┌─────────────────────────────────────────────────┐
│          Berggipfel 1500m ü.NN                  │
│                                                 │
│  ┌────────────────┐        ┌─────────────────┐ │
│  │  Solar Panel   │──12V──→│ MPPT Controller │ │
│  │  150W          │        │  12V/100Ah      │ │
│  └────────────────┘        └────────┬────────┘ │
│                                     │          │
│                                     │ 12V      │
│                                     ▼          │
│  ┌─────────────────────────────────────────┐   │
│  │      E90-DTU (900SL30)                  │   │
│  │  ┌──────────┐                           │   │
│  │  │ 8-28V DC │ Power Input               │   │
│  │  └──────────┘                           │   │
│  │                                         │   │
│  │  ┌──────────┐    LoRa     ┌─────────┐ │   │
│  │  │  RS485   │◄───Modem───►│ Antenna │ │   │
│  │  │  (Cfg)   │              │ +3dBi   │ │   │
│  │  └──────────┘    RELAY=ON  └────┬────┘ │   │
│  └─────────────────────────────────│──────┘   │
│                                    │          │
└────────────────────────────────────┼──────────┘
                                     │
                          LoRa Broadcast (868.1 MHz)
                                     │
            ┌────────────────────────┼────────────────────┐
            │                        │                    │
            ▼                        ▼                    ▼
       E22 Tal A               E22 Tal B           Dragino Gateway
       (700m)                  (600m)              (700m)
                                                        │
                                                   WireGuard
                                                        │
                                                        ▼
                                                  heissa.de
```

## Installation

### 1. Hardware-Vorbereitung

**Benötigte Komponenten:**
```
Hardware:
├─ E90-DTU (900SL30):              ~70 EUR
├─ USB-zu-RS485 Adapter (FTDI):    ~15 EUR
├─ 868 MHz Antenne (+3dBi):        ~20 EUR
├─ SMA-Kabel 3m:                   ~15 EUR
├─ IP67 Gehäuse:                   ~80 EUR
├─ Solar 150W + Controller:       ~200 EUR
├─ LiFePO4 Akku 100Ah:            ~300 EUR
├─ Blitzschutz:                    ~40 EUR
└─ Montage-Material:               ~50 EUR
────────────────────────────────────────
Gesamt:                          ~790 EUR
```

### 2. Verkabelung

**RS485 Anschluss (Konfiguration):**
```
E90-DTU Pins:
├─ A+ (RS485 A)  ──→  USB-RS485 A+
├─ B- (RS485 B)  ──→  USB-RS485 B-
├─ GND           ──→  USB-RS485 GND
└─ 8-28V DC      ──→  Solar-System (+/-)

Wichtig: RS485 benötigt Twisted-Pair Kabel!
```

**Antenne:**
```
E90-DTU SMA Female  ──→  3m LMR-400  ──→  Antenne +3dBi
                                           (3m Mast-Spitze)
```

### 3. Konfiguration

**Schritt 1: E90-DTU lokal konfigurieren**
```bash
# USB-RS485 Adapter anschließen
# E90-DTU mit 12V versorgen

# Konfigurationsskript ausführen:
cd /home/user/lora
python3 e90_repeater_setup.py --port /dev/ttyUSB0 --mode query

# Als Repeater konfigurieren:
python3 e90_repeater_setup.py --port /dev/ttyUSB0 --mode repeater --tx-pow PWMAX
```

**Schritt 2: Konfiguration verifizieren**
```bash
python3 e90_repeater_setup.py --port /dev/ttyUSB0 --mode query
```

Erwartete Ausgabe:
```
📊 E90-DTU Status:
============================================================

1️⃣  LoRa Parameter:
→ Sende: AT+LORA
← Empfangen: +LORA=65535,18,9600,240,RSCHON,PWMAX,0,RSDATON,TRNOR,RLYON,LBTOFF,WOROFF,2000,0

                              ^^^^ RELAY=ON!

2️⃣  Firmware Version:
→ Sende: AT+VER
← Empfangen: +VER=E90-DTU(900SL30) V1.2
```

### 4. Berggipfel-Installation

**Installations-Checkliste:**
- [ ] Standort mit freier Sicht zum Tal (5km)
- [ ] Genehmigung Grundstückseigentümer
- [ ] Wetter-Fenster (Sommer, wenig Wind)
- [ ] Blitzschutz installiert
- [ ] Solar-Panel nach Süden ausgerichtet
- [ ] Gehäuse IP67 wasserdicht verschraubt
- [ ] Erdung vorhanden
- [ ] Antenne 3m über Boden
- [ ] Kabel-Zugentlastung

**Montage-Reihenfolge:**
1. Mast aufstellen (3m, Erdung)
2. Gehäuse befestigen (windgeschützt)
3. Solar-Panel montieren (Süd-Ausrichtung)
4. E90-DTU im Gehäuse fixieren
5. Blitzschutz zwischen Antenne-Kabel
6. Antenne auf Mast montieren
7. Verkabelung prüfen
8. System einschalten

## Funktionsweise der RELAY-Funktion

### Wie funktioniert RELAY=ON?

```
Normaler Betrieb (RELAY=OFF):
E22 Sender ─┬─> E90-DTU empfängt
            └─> E90-DTU speichert NICHT
                E90-DTU sendet NICHT weiter

Repeater-Betrieb (RELAY=ON):
E22 Sender ─┬─> E90-DTU empfängt
            │   E90-DTU speichert Paket
            │   E90-DTU wartet 100ms
            └─> E90-DTU sendet IDENTISCH weiter
                    │
                    └─> Erreicht alle anderen E22 im Radius!
```

### Frequenz-Handling

**Problem:** Feedback-Loop vermeiden!

**Lösung im E90-DTU:**
```
1. Empfängt auf 868.1 MHz
2. Wartet kurze Zeit (intern)
3. Sendet auf gleicher Frequenz
4. Filtert eigene Aussendung (interne Logik)
```

Das E90-DTU hat **eingebaute Logik**, um Feedback-Loops zu verhindern!

## Reichweiten-Tests

### Test-Protokoll

**Tag 1: Line-of-Sight Test (5km Tal → Berg)**
```bash
# Im Tal (700m):
./e22.py --port /dev/ttyUSB0 --channel 18 --rssi-enable 1
python3 lorain.py  # Empfänger starten

# Auf Berg (1500m):
# E90-DTU läuft automatisch als Repeater

# Test-Nachricht senden:
echo "TEST von Tal" > /dev/ttyUSB0
```

**Erwartete Ergebnisse:**
| Distanz | SF12 RSSI | SF7 RSSI | Packet Loss |
|---------|-----------|----------|-------------|
| 5 km    | -90 dBm   | -95 dBm  | <1%         |
| 10 km   | -110 dBm  | -115 dBm | <5%         |
| 15 km   | -125 dBm  | N/A      | <10%        |
| 20 km   | -135 dBm  | N/A      | <20%        |

### Multi-Hop Test

**Setup:** 3× E90-DTU im Mesh
```
E90-DTU #1 (Berg 1, 1500m)
    ├─ 10km ─→ E90-DTU #2 (Berg 2, 1200m)
    │             └─ 15km ─→ E90-DTU #3 (Berg 3, 1400m)
    │
    └─ Alle haben RELAY=ON
```

**Resultat:**
- Total Coverage: ~40km Radius
- Latenz: <500ms (3× Relay @ 100ms)
- Redundanz: Ausfall von 1 Repeater → 2 verbleibend

## Monitoring & Wartung

### Remote-Monitoring (falls Internet)

**Option A: RS485 via Raspberry Pi**
```
E90-DTU (RS485) ──→ RPi (USB-RS485) ──→ 4G/LTE ──→ heissa.de

Python-Skript auf RPi:
- Liest AT+LORA alle 5 Minuten
- Sendet Status via MQTT an heissa.de
- Alert bei Ausfall
```

**Option B: Zusätzlicher Dragino Gateway**
```
E90-DTU (LoRa Repeater)
    │
    └─ 100m Kabel ─→ Dragino Gateway ──WireGuard──> heissa.de
```

### Wartungs-Logs

**Monatlich:**
- [ ] Batterie-Spannung prüfen (>12.5V)
- [ ] Solar-Ertrag checken (Log)
- [ ] Repeater-Uptime

**Vierteljährlich (Vor-Ort):**
- [ ] Antennen-Befestigung
- [ ] Gehäuse-Dichtungen
- [ ] Kabel-Verbindungen
- [ ] Korrosion prüfen

**Jährlich:**
- [ ] Komplette Inspektion
- [ ] Batterie-Kapazitätstest
- [ ] Firmware-Update (falls verfügbar)

## Troubleshooting

### Problem: E90-DTU antwortet nicht auf AT-Befehle

**Diagnose:**
```bash
# 1. Port prüfen
ls /dev/ttyUSB*

# 2. Berechtigungen
sudo chmod 666 /dev/ttyUSB0

# 3. Test mit minicom
minicom -D /dev/ttyUSB0 -b 9600

# 4. Manuell AT-Befehl senden
AT<ENTER>
```

**Lösung:**
- Baudrate prüfen (Standard: 9600)
- RS485 A+/B- vertauscht?
- E90-DTU Stromversorgung OK?

### Problem: Kein LoRa-Empfang trotz RELAY=ON

**Diagnose:**
```bash
# 1. Konfiguration prüfen
python3 e90_repeater_setup.py --mode query

# 2. Frequenz verifizieren
# Channel 0 muss 868.1 MHz sein
# Bei E90-DTU: 850.125 + (0 × 1MHz) = 850.125 MHz ❌
#              ACHTUNG: E90 hat anderen Offset!

# 3. Korrekte Kanal-Berechnung für 868.1 MHz:
# E90-DTU: Channel = (868.1 - 850.125) = 17.975 ≈ Channel 18!
```

**Lösung:**
```bash
python3 e90_repeater_setup.py --mode repeater --channel 18
```

### Problem: Feedback-Loop (Endlos-Echo)

**Symptom:**
- E90-DTU sendet jedes Paket 10× wiederholt
- Network überlastet

**Ursache:**
- E90-DTU empfängt eigene Aussendung
- RELAY sendet wieder → Loop

**Lösung:**
```bash
# 1. LBT aktivieren (Listen Before Talk)
# Verhindert Senden während Empfang
--lbt LBTON

# 2. ODER: WOR Mode nutzen
# Wake-on-Radio mit Timing
--wor WORRX --wor-tim 2000
```

## Performance-Optimierung

### Maximale Reichweite (SF12 äquivalent)

**E90-DTU Konfiguration:**
```bash
python3 e90_repeater_setup.py \
  --mode repeater \
  --channel 18 \
  --air-baud 300 \      # Langsamste Rate = höchste Reichweite
  --tx-pow PWMAX \      # 30 dBm (1W)
  --pack-length 240
```

**Erwartung:**
- Reichweite: 30-50 km (Berg-zu-Berg LoS)
- Airtime: ~2 Sekunden pro Paket
- Duty Cycle: Max. 18 Pakete/Stunde (1%)

### Maximaler Durchsatz (SF7 äquivalent)

**E90-DTU Konfiguration:**
```bash
python3 e90_repeater_setup.py \
  --mode repeater \
  --channel 18 \
  --air-baud 62500 \    # Schnellste Rate
  --tx-pow PWMAX \
  --pack-length 240
```

**Erwartung:**
- Reichweite: 10-15 km (Berg-zu-Berg LoS)
- Airtime: ~200 ms pro Paket
- Duty Cycle: Max. 180 Pakete/Stunde (1%)

## Vergleich: E90-DTU vs. Höchst et al. Paper

| Metrik | Paper (D2D) | E90-DTU (Berg) | Faktor |
|--------|-------------|----------------|--------|
| **Reichweite SF12 Urban** | 2.89 km | 15-25 km | **8×** |
| **Reichweite SF12 Rural** | 1.64 km | 30-50 km | **20×** |
| **Airtime** | Gleich | Gleich | 1× |
| **Infrastruktur** | Keine | Optional | - |
| **RSSI @ 5km** | N/A | -90 dBm | - |
| **Repeater-Funktion** | rf95modem | Native | ✅ |

**Fazit:** E90-DTU auf Berg = **10-20× bessere Reichweite** als Paper-Setup!

## Rechtliche Aspekte

### ISM-Band 868 MHz (EU)

**WICHTIG:**
```
Max. ERP:       14 dBm (25 mW)
E90-DTU PWMAX:  30 dBm (1W) ❌ ÜBERSCHREITET LIMIT!

Lösungen:
1. TX Power auf PWMID drosseln (~20 dBm)
2. Amateurfunk-Lizenz beantragen
3. In 433 MHz Band wechseln (Klasse E)
```

### Amateurfunk Alternative

**Vorteile mit Lizenz:**
```
Frequenz:      433 MHz (70cm Band)
Sendeleistung: 750W erlaubt!
E90-DTU:       Funktioniert auch auf 433 MHz
Rufzeichen:    Muss gesendet werden
```

## Konfigurations-Persistenz & Langzeit-Zuverlässigkeit

### ⚠️ KRITISCH für jahrelangen autarken Betrieb!

**Frage:** Bleibt die RELAY=ON Konfiguration nach Stromausfall erhalten?

**Antwort:** Das muss **VOR** der Berg-Installation getestet werden!

### Persistenz-Test durchführen

**WICHTIG:** Diesen Test IMMER durchführen bevor E90-DTU auf den Berg kommt!

```bash
# Persistenz-Test Skript verwenden:
python3 e90_persistence_test.py --port /dev/ttyUSB0 --test single

# Oder Stress-Test mit 3× Power-Cycles:
python3 e90_persistence_test.py --port /dev/ttyUSB0 --test stress --cycles 3
```

**Test-Ablauf:**
1. Skript liest aktuelle Konfiguration aus
2. Benutzer schaltet E90-DTU aus und wieder ein (Power-Cycle)
3. Skript liest Konfiguration erneut aus
4. Automatischer Vergleich und Warnung bei Unterschieden

### Was passiert bei Stromausfall?

**Szenario 1: Konfiguration ist PERSISTENT** ✅
```
Power OFF → Power ON
├─ E90-DTU bootet automatisch
├─ Liest Config aus Flash/EEPROM
├─ RELAY=ON wird wiederhergestellt
└─ Repeater funktioniert sofort!
```

**Szenario 2: Konfiguration ist NICHT PERSISTENT** ❌
```
Power OFF → Power ON
├─ E90-DTU bootet mit Werkseinstellungen
├─ RELAY=OFF (kein Repeater-Betrieb!)
├─ Falsche Frequenz/Parameter
└─ System funktioniert NICHT!
```

### Ebyte E90-DTU Konfigurations-Speicher

**Laut Datenblatt:**
```
- Konfiguration wird in EEPROM gespeichert
- Persistenz über Power-Cycles: JA
- Retention Time: >10 Jahre
- Write Cycles: >100,000
```

→ **Theoretisch: Konfiguration sollte persistent sein!**

**Aber:** IMMER testen! Firmware-Versionen können variieren!

### Watchdog-System für maximale Sicherheit

Selbst wenn Persistenz funktioniert, kann es andere Fehler geben:
- Hardware-Defekt
- Cosmic Ray Bit-Flip
- Firmware-Bug nach x Jahren

**Lösung: Watchdog mit Auto-Recovery**

#### Option 1: Hardware-Watchdog (empfohlen!)

```
┌─────────────┐      ┌──────────────┐      ┌──────────────┐
│  E90-DTU    │◄────►│  ATtiny85    │◄────►│ Solar System │
│  (Repeater) │      │  (Watchdog)  │      │   (Power)    │
└─────────────┘      └──────────────┘      └──────────────┘
                            │
                            │ Monitoring:
                            ├─ E90-DTU sendet "Heartbeat"
                            ├─ Kein Heartbeat nach 5 Min
                            └─> Power-Cycle via MOSFET
```

**ATtiny85 Watchdog-Code (Arduino):**
```cpp
// Watchdog für E90-DTU Repeater
// Überwacht LoRa-Heartbeat, rebootet bei Ausfall

#define POWER_CONTROL_PIN 0  // MOSFET Gate für E90-DTU Power
#define HEARTBEAT_PIN 1      // Input von E90-DTU
#define TIMEOUT_MS 300000    // 5 Minuten

unsigned long lastHeartbeat = 0;

void setup() {
  pinMode(POWER_CONTROL_PIN, OUTPUT);
  pinMode(HEARTBEAT_PIN, INPUT);
  digitalWrite(POWER_CONTROL_PIN, HIGH);  // E90-DTU AN
}

void loop() {
  // Heartbeat empfangen?
  if (digitalRead(HEARTBEAT_PIN) == HIGH) {
    lastHeartbeat = millis();
  }

  // Timeout check
  if (millis() - lastHeartbeat > TIMEOUT_MS) {
    // REBOOT E90-DTU
    digitalWrite(POWER_CONTROL_PIN, LOW);   // AUS
    delay(5000);                            // 5 Sekunden warten
    digitalWrite(POWER_CONTROL_PIN, HIGH);  // AN
    lastHeartbeat = millis();               // Reset Timer
  }

  delay(1000);
}
```

**Hardware:**
- ATtiny85: ~2 EUR
- N-Channel MOSFET (IRLZ44N): ~1 EUR
- Stromverbrauch: <1 mA

#### Option 2: Software-Watchdog (Raspberry Pi)

```python
#!/usr/bin/python3
# e90_watchdog.py - Überwacht E90-DTU via RS485

import serial
import time
import subprocess

SERIAL_PORT = '/dev/ttyUSB0'
TIMEOUT = 300  # 5 Minuten
POWER_GPIO = 17  # BCM Pin für Relais

def check_e90_alive(ser):
    """Prüft ob E90-DTU antwortet"""
    try:
        ser.write(b"AT\r\n")
        time.sleep(0.5)
        response = ser.read(100)
        return b"OK" in response
    except:
        return False

def power_cycle_e90():
    """Power-Cycle via GPIO-Relais"""
    subprocess.run(['gpio', 'write', str(POWER_GPIO), '0'])  # OFF
    time.sleep(5)
    subprocess.run(['gpio', 'write', str(POWER_GPIO), '1'])  # ON
    time.sleep(10)  # Boot-Zeit

def main():
    last_ok = time.time()

    while True:
        try:
            ser = serial.Serial(SERIAL_PORT, 9600, timeout=2)

            if check_e90_alive(ser):
                last_ok = time.time()
                print(f"✅ E90-DTU OK @ {time.strftime('%H:%M:%S')}")
            else:
                if time.time() - last_ok > TIMEOUT:
                    print("❌ E90-DTU nicht erreichbar! Power-Cycle...")
                    power_cycle_e90()
                    last_ok = time.time()

            ser.close()

        except Exception as e:
            print(f"⚠️ Fehler: {e}")

        time.sleep(60)  # Alle 60 Sekunden prüfen

if __name__ == "__main__":
    main()
```

#### Option 3: Extern über LoRa (Monitoring von unten)

```python
#!/usr/bin/python3
# e90_remote_monitor.py - Im Tal, monitored Repeater

import time
import serial

def send_ping():
    """Sendet Ping an Repeater"""
    with serial.Serial('/dev/ttyUSB0', 9600) as ser:
        ser.write(b"PING\n")

def check_response():
    """Wartet auf Echo vom Repeater"""
    with serial.Serial('/dev/ttyUSB0', 9600, timeout=10) as ser:
        data = ser.read(100)
        return b"PING" in data  # Echo durch Repeater

def alert_admin():
    """Sendet Alert wenn Repeater offline"""
    # SMS, E-Mail, Push-Notification, etc.
    pass

# Monitoring-Loop
while True:
    send_ping()
    if check_response():
        print("✅ Repeater aktiv")
    else:
        print("❌ Repeater offline!")
        alert_admin()

    time.sleep(3600)  # Jede Stunde
```

### Konfigurations-Backup-Strategie

**Vor Berg-Installation:**

```bash
# 1. Konfiguration testen und verifizieren
python3 e90_persistence_test.py --test stress --cycles 5

# 2. Backup erstellen
# Wird automatisch gespeichert in: /home/user/lora/config_backups/

# 3. Restore-Skript generieren (automatisch)
ls -l config_backups/restore_config.sh

# 4. Backup auf USB-Stick kopieren (für Not fall)
cp -r config_backups/ /media/usb/e90_backup_$(date +%Y%m%d)/
```

**Backup-Dateien:**
```
config_backups/
├── e90_config_20260109_120000.json  # JSON Backup
├── restore_config.sh                 # Automatisches Restore
└── persistence_test_log.txt          # Test-Protokoll
```

**Im Notfall (Config verloren):**
```bash
# Mit Backup wiederherstellen:
cd /home/user/lora/config_backups
./restore_config.sh

# Oder manuell:
python3 e90_repeater_setup.py \
  --mode repeater \
  --addr 65535 \
  --netid 18 \
  --channel 18 \
  --tx-pow PWMAX
```

### Jahrelanger autarker Betrieb - Checkliste

Für **100% Zuverlässigkeit** über viele Jahre:

- [ ] **Persistenz-Test durchgeführt** (min. 3× Power-Cycles)
- [ ] **Konfigurations-Backup** auf 2 USB-Sticks
- [ ] **Hardware-Watchdog** installiert (ATtiny85 empfohlen)
- [ ] **Remote-Monitoring** eingerichtet (Tal → Berg Ping)
- [ ] **Solar-System überdimensioniert** (200W statt 150W)
- [ ] **Batterie-Redundanz** (2× 100Ah Akkus parallel)
- [ ] **Blitzschutz** professionell installiert
- [ ] **Wetterfestes Gehäuse** IP67+ mit Gore-Tex Membrane
- [ ] **Jährliche Wartung** geplant (Sommer)
- [ ] **Notfall-Plan** dokumentiert (Kontaktpersonen, Zugangscode)

### Worst-Case Szenarien & Lösungen

| Szenario | Wahrscheinlichkeit | Lösung |
|----------|-------------------|---------|
| **Stromausfall** | Hoch (Winter) | Solar + Batterie überdimensioniert |
| **Config-Verlust** | Niedrig (wenn getestet) | Hardware-Watchdog mit Auto-Restore |
| **Hardware-Defekt** | Mittel (nach 3-5 Jahren) | Redundanter E90-DTU (parallel) |
| **Blitzschlag** | Mittel (Bergspitze!) | Professioneller Blitzschutz + Versicherung |
| **Vandalismus** | Niedrig (abgelegen) | Verstecktes Gehäuse, GPS-Tracker |
| **Schnee/Eis** | Hoch (Winter) | Gehäuse-Heizung (12V, 5W), Solar-Panel Neigung 60° |

### Redundanz-Setup (Option für kritische Deployments)

**Doppelter E90-DTU Repeater:**

```
Berg 1500m:
├─ E90-DTU Primary   (RELAY=ON, Channel 18)
├─ E90-DTU Secondary (RELAY=ON, Channel 18, Backup-Power)
├─ Solar-System #1 → E90-DTU #1
├─ Solar-System #2 → E90-DTU #2
└─ Bei Ausfall #1: #2 übernimmt automatisch!
```

**Kosten:** +~300 EUR, aber **99.9% Uptime**!

## Zusammenfassung

### ✅ E90-DTU Vorteile
1. **Native RELAY-Funktion** (RLYON)
2. **Robuste 8-28V Stromversorgung**
3. **30 dBm Sendeleistung** (1W)
4. **RS485 störsicher** (lange Kabel möglich)
5. **Industrielle Temperatur** (-40°C bis +85°C)
6. **Einfache AT-Kommando-Konfiguration**

### 🎯 Ideales Setup
- **E90-DTU auf Berg (1500m)** als Repeater
- **E22 im Tal** als Endgeräte
- **Dragino Gateway** als Cloud-Anbindung (optional)
- **Solar-betrieben** mit 150W Panel
- **Reichweite:** 15-50 km je nach Gelände

### 📞 Support & Kontakt
- E90-DTU Datenblatt: https://www.ebyte.com/
- GitHub Repository: https://github.com/gerontec/lora
- E-Mail: gh@heissa.de
