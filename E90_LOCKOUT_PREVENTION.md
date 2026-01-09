# E90-DTU Lockout-Prevention Guide

## ⚠️ KRITISCH: Remote-Konfiguration kann dich AUSSPERREN!

Bei einem autarken System auf 1500m Höhe ist ein Lockout **katastrophal**:
- Physischer Zugang nur zu Fuß/mit Bergausrüstung
- Im Winter eventuell unmöglich
- Kosten: Zeit, Geld, Gefahr

## 🚫 Lockout-Szenarien

### Szenario 1: Baudrate-Änderung (HÄUFIGSTER Fehler!)

**Risiko:**
```bash
# Du sendest über RS485:
AT+UART=115200,8,1,0\r\n

# E90-DTU wechselt sofort auf 115200 Baud
# Deine Verbindung läuft noch auf 9600 Baud
# → AB JETZT: Keine Kommunikation mehr möglich!
```

**Symptom:**
- AT-Befehle werden gesendet, aber keine Antwort
- Gibberish oder Timeout
- Device "scheint tot"

**Lösung:**
```bash
# MUSS mit neuer Baudrate neu verbinden:
python3 e90_repeater_setup.py --port /dev/ttyUSB0 --baudrate 115200
```

**Prävention:**
```bash
# NIEMALS Baudrate remote ändern!
# Wenn doch, dann:
1. Immer dokumentieren BEVOR man sendet
2. Zweite serielle Verbindung parallel (Backup)
3. Auto-Revert nach 60 Sekunden (siehe unten)
```

### Szenario 2: Falsche Frequenz/Kanal

**Risiko:**
```bash
# Aktuell: Channel 18 (868.1 MHz)
AT+LORA=...,99,...\r\n  # Ändert auf ungültigen Kanal

# E90-DTU ist jetzt auf falscher Frequenz
# Deine E22 im Tal können nicht mehr empfangen
# → KEIN LoRa-Kontakt mehr!
```

**Symptom:**
- E90-DTU antwortet nicht mehr auf LoRa
- Keine Pakete kommen durch
- Repeater scheint "tot"

**Lösung:**
```bash
# Physisch zum Berg hochklettern
# RS485 direkt anschließen
# Konfiguration zurücksetzen
```

**Prävention:**
- Nur getestete Kanäle verwenden (18 = 868.1 MHz)
- Frequenz-Liste immer dabei haben
- Backup-Frequenz definieren

### Szenario 3: Adress-Filter aktiviert

**Risiko:**
```bash
# Aktuell: Address = 65535 (empfängt ALLE)
AT+LORA=12345,...\r\n  # Ändert auf spezifische Adresse

# E90-DTU hört nur noch auf Pakete mit Ziel-Adresse 12345
# Deine E22 senden an Broadcast (65535)
# → E90-DTU ignoriert alle Pakete!
```

**Lösung:**
- E22 müssen Fixed-Transmission Mode nutzen mit Target=12345
- Oder physischer Zugang zum Berg

**Prävention:**
- **IMMER** Address = 65535 (Broadcast) für Repeater!
- Dokumentieren wenn anders

### Szenario 4: Verschlüsselung ohne Key

**Risiko:**
```bash
AT+LORA=...,12345\r\n  # Setzt Crypt-Key auf 12345

# E90-DTU akzeptiert nur noch verschlüsselte Pakete
# Deine E22 senden unverschlüsselt
# → Alle Pakete werden verworfen!
```

**Lösung:**
- E22 mit gleichem Key konfigurieren: `--write-key 0x12 0x34`
- Oder Factory Reset

**Prävention:**
- Verschlüsselung nur wenn nötig
- Key IMMER dokumentieren
- Key-Backup auf USB-Stick

### Szenario 5: Power-Mode Änderung

**Risiko:**
```bash
AT+LORA=...,WORRX,...\r\n  # Wake-on-Radio RX Mode

# E90-DTU geht in Sleep nach jedem Paket
# Wacht nur in bestimmten Intervallen auf
# → Meiste Zeit NICHT erreichbar!
```

**Lösung:**
- Warten auf Wake-Fenster
- Oder physischer Reset

**Prävention:**
- **IMMER** WOR=WOROFF für Repeater!
- Dauerbetrieb = kritisch für Repeater

### Szenario 6: RS485 Parameter ändern

**Risiko:**
```bash
# Wenn E90-DTU RS485-Modus hat (manche Varianten):
AT+RS485=...DISABLE...\r\n

# RS485 wird deaktiviert
# → Keine serielle Kommunikation mehr möglich!
```

**Lösung:**
- Factory Reset (Hardware)

### Szenario 7: Firmware-Update fehlschlägt

**Risiko:**
```bash
# Remote Firmware-Update über LoRa
# Update bricht ab (Stromausfall, Verbindungsfehler)
# → Device ist "gebricked"
```

**Lösung:**
- JTAG/ISP Programmer (sehr aufwendig)
- Device-Austausch

**Prävention:**
- **NIEMALS** Remote Firmware-Updates!
- Nur vor Ort mit stabiler Stromversorgung

## 🛡️ Lockout-Prevention Strategien

### Strategie 1: "Watchdog mit Auto-Revert"

**Konzept:**
```
1. Sende neue Konfiguration
2. E90-DTU aktiviert neue Config
3. Warte 60 Sekunden
4. Wenn KEIN "CONFIRM"-Befehl kommt:
   → Automatisch zurück zu alter Config!
```

**Implementierung:**

Das E90-DTU hat **KEINE** eingebaute Auto-Revert-Funktion!

**Workaround: Externe Watchdog-Logik**

```python
#!/usr/bin/python3
# e90_safe_remote_config.py - Sichere Remote-Konfiguration

import serial
import time
import json

BACKUP_FILE = 'e90_config_backup.json'
REVERT_TIMEOUT = 60  # Sekunden

def save_current_config(ser):
    """Speichert aktuelle Config als Backup"""
    response = send_at(ser, "AT+LORA\r\n")
    # Parse und speichern
    with open(BACKUP_FILE, 'w') as f:
        json.dump({'config': response}, f)
    print("✅ Backup gespeichert")

def apply_new_config(ser, new_config):
    """Wendet neue Config an"""
    cmd = f"AT+LORA={new_config}\r\n"
    response = send_at(ser, cmd)
    print(f"📤 Neue Config gesendet: {response}")

def wait_for_confirmation(timeout):
    """Wartet auf Benutzer-Bestätigung"""
    print(f"\n⏳ Du hast {timeout} Sekunden zum Testen!")
    print("   Drücke ENTER wenn neue Config OK")
    print("   Oder warte ab → Auto-Revert zu alter Config")

    import select
    rlist, _, _ = select.select([sys.stdin], [], [], timeout)

    if rlist:
        return True  # Benutzer hat bestätigt
    else:
        return False  # Timeout → Revert

def revert_to_backup(ser):
    """Stellt Backup-Config wieder her"""
    with open(BACKUP_FILE, 'r') as f:
        backup = json.load(f)

    # Config aus Backup extrahieren und wiederherstellen
    print("⚠️ REVERTING zu Backup-Config...")
    # ... Implementierung ...

# Hauptablauf:
ser = serial.Serial('/dev/ttyUSB0', 9600)

# 1. Backup erstellen
save_current_config(ser)

# 2. Neue Config anwenden
apply_new_config(ser, "65535,18,9600,...")

# 3. Warten auf Bestätigung
if wait_for_confirmation(REVERT_TIMEOUT):
    print("✅ Neue Config bestätigt!")
else:
    # 4. Auto-Revert
    revert_to_backup(ser)
    print("✅ Zurück zu alter Config!")
```

**Problem:** Funktioniert nur wenn RS485-Verbindung noch funktioniert!

### Strategie 2: Hardware-Watchdog mit Config-Reset

**Konzept:**
```
ATtiny85 Watchdog:
├─ Überwacht E90-DTU Heartbeat
├─ Bei Ausfall nach 5 Minuten:
│  ├─ Power-Cycle E90-DTU
│  └─ ZUSÄTZLICH: Factory Reset Trigger!
└─ E90-DTU bootet mit Werkseinstellungen
   → RS485 auf Standard-Baudrate 9600!
```

**Hardware:**
```
ATtiny85 ──┬──> MOSFET (Power-Cycle)
           └──> GPIO Pin zu E90-DTU RESET-Pin (falls vorhanden)
```

**Code-Erweiterung:**
```cpp
#define FACTORY_RESET_PIN 2  // Verbindung zu E90-DTU RESET

void factory_reset_e90() {
  // Trigger Hardware-Reset
  digitalWrite(FACTORY_RESET_PIN, LOW);
  delay(1000);  // 1 Sekunde halten
  digitalWrite(FACTORY_RESET_PIN, HIGH);

  // E90-DTU bootet mit Factory Defaults
  // Baudrate: 9600, Address: 65535, etc.
}

void loop() {
  if (millis() - lastHeartbeat > TIMEOUT_MS) {
    // Option A: Nur Power-Cycle (Config bleibt erhalten)
    power_cycle_e90();

    // Option B: Factory Reset (nur wenn mehrfach fehlgeschlagen)
    failureCount++;
    if (failureCount > 3) {
      factory_reset_e90();
      failureCount = 0;
    }
  }
}
```

### Strategie 3: Dual-Config System

**Konzept:**
```
E90-DTU #1: Production Config (RELAY=ON, Channel 18)
E90-DTU #2: Backup Config (Channel 23, Management-Only)

Wenn #1 nicht mehr erreichbar:
→ Kommunikation über #2
→ #1 kann über #2 neu konfiguriert werden
```

**Setup:**
```
Berg 1500m:
├─ E90-DTU #1 (Primary Repeater)
│  └─ Channel 18 (868.1 MHz), RELAY=ON
│
└─ E90-DTU #2 (Management Backup)
   └─ Channel 23 (868.6 MHz), RELAY=OFF
   └─ RS485 verbunden mit #1 (kann #1 neu konfigurieren!)
```

**Ablauf bei Lockout von #1:**
```bash
1. Wechsel E22 im Tal auf Channel 23
2. Kommunikation mit E90-DTU #2
3. #2 sendet AT-Befehle über RS485 an #1
4. #1 wird neu konfiguriert
5. #1 ist wieder erreichbar auf Channel 18!
```

**Kosten:** +70 EUR (ein zweites E90-DTU), aber **100% Lockout-Schutz!**

### Strategie 4: "Safe Mode" Frequenz

**Konzept:**
```
Normale Operation:  Channel 18 (868.1 MHz) - Repeater
Safe Mode:          Channel 10 (867.5 MHz) - Management

Bei Problemen:
1. E90-DTU wechselt automatisch alle 10 Minuten kurz auf Channel 10
2. Lauscht auf Management-Befehle
3. Kann neu konfiguriert werden
4. Wechselt zurück zu Channel 18
```

**Problem:** E90-DTU hat KEINE eingebaute Safe-Mode Funktion!

**Lösung:** Externes Microcontroller (ESP32/Arduino) mit 2× E90-DTU:
```
Arduino Nano:
├─ Verbunden mit E90-DTU via RS485
├─ Sendet periodisch Channel-Wechsel-Befehle
├─ Channel 18 (9 Minuten) → Channel 10 (1 Minute) → Repeat
└─ Ermöglicht Management-Zugang alle 10 Minuten
```

### Strategie 5: Factory Reset Methode (Hardware)

**E90-DTU Factory Reset:**

Laut Datenblatt (muss verifiziert werden!):
```
Methode 1: Reset-Pin
- RESET-Pin für 5+ Sekunden auf GND
- Device bootet mit Werkseinstellungen

Methode 2: Boot-Mode
- Bestimmte Pin-Kombination beim Boot
- Triggert Factory Reset

Methode 3: AT-Command (wenn noch erreichbar)
- AT+RESTORE\r\n
- oder AT+RESET=FACTORY\r\n
```

**Remote-Trigger (falls möglich):**
```
GPIO-Pin von ATtiny85 ──> E90-DTU RESET-Pin

Bei mehrfachem Heartbeat-Ausfall:
→ ATtiny85 triggert Hardware-Reset
→ E90-DTU kehrt zu Werkseinstellungen zurück
```

## 📋 Best Practices für Remote-Config

### Regel 1: Niemals blind remote konfigurieren!

```bash
# ❌ FALSCH:
python3 e90_repeater_setup.py --mode repeater --channel 99

# ✅ RICHTIG:
1. Config lokal auf Testgerät ausprobieren
2. Testen ob Kommunikation funktioniert
3. Erst dann remote anwenden
```

### Regel 2: Immer Backup vor Änderungen

```bash
# Vor JEDER Remote-Config:
python3 e90_persistence_test.py --mode query > backup_$(date +%Y%m%d_%H%M%S).txt
```

### Regel 3: Dokumentation ist Pflicht

**Config-Logbuch führen:**
```
config_log.txt:
─────────────────────────────────────
2026-01-09 12:00: Initial Setup
  - Address: 65535
  - Channel: 18 (868.1 MHz)
  - Air Baud: 9600
  - RELAY: ON
  - Baudrate RS485: 9600
─────────────────────────────────────
2026-01-15 14:30: Power erhöht
  - TX Power: PWMID → PWMAX
  - Grund: Bessere Reichweite gewünscht
  - Test: OK, RSSI verbessert um 3 dBm
─────────────────────────────────────
```

### Regel 4: Nie kritische Parameter remote ändern

**Verbotene Remote-Änderungen:**
- ❌ Baudrate (RS485/UART)
- ❌ Frequenz/Kanal (außer zu getesteten Werten)
- ❌ Address (außer zurück zu 65535)
- ❌ Verschlüsselung aktivieren
- ❌ WOR-Mode aktivieren
- ❌ Firmware-Update

**Erlaubte Remote-Änderungen:**
- ✅ TX Power (PWMAX ↔ PWMID)
- ✅ LBT ON/OFF
- ✅ Air Baud Rate (zu getesteten Werten)
- ✅ RSSI Enable ON/OFF

### Regel 5: Zweistufiges Änderungs-Protokoll

```bash
Stufe 1: Ankündigung (1 Tag vorher)
─────────────────────────────────────
"Morgen 14:00 Uhr: Erhöhung TX Power auf PWMAX"
- Test-Zeitfenster: 14:00-15:00 Uhr
- Backup vorhanden: YES
- Rollback-Plan: Revert zu PWMID bei Problemen

Stufe 2: Durchführung
─────────────────────────────────────
14:00: Config-Backup erstellt
14:05: Neue Config angewendet
14:06: Test: Sende Ping von Tal
14:07: Ping empfangen! RSSI: -87 dBm (vorher: -90 dBm)
14:10: Bestätigung: Neue Config OK!
```

## 🚨 Emergency Recovery Procedures

### Recovery Level 1: RS485 noch erreichbar

```bash
# Wenn RS485-Verbindung noch funktioniert:
python3 e90_repeater_setup.py --mode query  # Status prüfen

# Wenn Baudrate falsch:
for baud in 9600 19200 38400 57600 115200; do
  echo "Teste Baudrate $baud..."
  python3 e90_repeater_setup.py --port /dev/ttyUSB0 --baudrate $baud --mode query
done

# Wenn erfolgreich → Backup wiederherstellen
cd config_backups
./restore_config.sh
```

### Recovery Level 2: LoRa noch erreichbar (aber falsche Config)

```bash
# Wenn E90-DTU auf falscher Frequenz:
# Systematisch alle EU868 Kanäle durchprobieren:

for channel in 0 1 2 3 10 18 23; do
  echo "Teste Channel $channel..."
  ./e22.py --channel $channel
  python3 lorain.py &  # Empfänger starten
  sleep 30
  # Manuell prüfen ob Pakete ankommen
  killall python3
done
```

### Recovery Level 3: Physischer Zugang erforderlich

```bash
# Berg-Expedition planen:
- [ ] Werkzeug: Schraubendreher, Zange
- [ ] USB-RS485 Adapter
- [ ] Laptop mit vorinstallierten Tools
- [ ] Config-Backups auf USB-Stick
- [ ] Factory-Reset Anleitung ausgedruckt
- [ ] Notfall-Telefonnummer Bergwacht
- [ ] Wettervorhersage gecheckt
- [ ] Zweite Person als Sicherung
```

**Am Berg:**
```bash
1. Gehäuse öffnen
2. USB-RS485 direkt an E90-DTU
3. Laptop anschließen
4. Factory Reset durchführen:
   AT+RESTORE\r\n  # oder Hardware-Reset
5. Backup-Config wiederherstellen
6. Testen!
7. Gehäuse schließen
```

### Recovery Level 4: Hardware-Defekt

```
Wenn alles fehlschlägt:
1. E90-DTU ausbauen
2. Ersatz-Device installieren (aus Backup-Box)
3. Mit Backup-Config konfigurieren
4. Defektes Device nach Hause mitnehmen
5. Im Labor debuggen/reparieren
```

## 🎯 Zusammenfassung: Lockout vermeiden

### ✅ DO's

1. **Immer lokal testen** bevor remote anwenden
2. **Backup vor jeder Änderung**
3. **Dokumentation führen**
4. **Watchdog-System** installieren
5. **Dual-Config System** für kritische Deployments
6. **Recovery-Plan** bereithalten
7. **Ersatz-Hardware** vorrätig

### ❌ DON'Ts

1. **NIEMALS** Baudrate remote ändern
2. **NIEMALS** ungetestete Kanäle remote setzen
3. **NIEMALS** Verschlüsselung blind aktivieren
4. **NIEMALS** WOR-Mode ohne Plan aktivieren
5. **NIEMALS** ohne Backup konfigurieren
6. **NIEMALS** ohne Dokumentation arbeiten
7. **NIEMALS** Firmware remote updaten

### 🆘 Im Zweifel

**LIEBER EINMAL ZU VIEL ZUM BERG HOCHKLETTERN ALS RISIKO EINGEHEN!**

Eine Berg-Expedition kostet:
- Zeit: 4-6 Stunden
- Geld: ~50 EUR (Transport, Verpflegung)
- Risiko: Minimal bei gutem Wetter

Ein Lockout kostet:
- Zeit: 4-6 Stunden + Frustration
- Geld: Gleich
- Risiko: Bei schlechtem Wetter gefährlich!

→ **Prävention ist billiger als Reparatur!**
