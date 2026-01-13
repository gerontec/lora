# E22 Script Improvements

## Verbesserungen gegenüber dem Original matthias-bs/loraE22

Basierend auf der offiziellen Ebyte E22 Dokumentation wurde das Python-Script mit folgenden Verbesserungen erweitert:

### 🐛 Bug-Fixes

1. **Hardcoded Sub-Packet Size**
   - ❌ **Original:** Sub-Packet immer auf `'240B'` hardcoded in `encodeConfig()`
   - ✅ **Verbessert:** Sub-Packet Size ist jetzt konfigurierbar über `sub_packet` Parameter
   - Unterstützt: 240B, 128B, 64B, 32B

2. **Fehlender Sub-Packet in Config**
   - ❌ **Original:** `config['subpckt']` nicht in `__init__` initialisiert
   - ✅ **Verbessert:** Vollständige Initialisierung aller Config-Parameter

3. **LBT Tippfehler**
   - ❌ **Original:** `LBT = { 0:'disable', 1:'disabe' }` (Tippfehler!)
   - ✅ **Verbessert:** `LBT = { 0:'disable', 1:'enable' }`

### ✨ Neue Features

4. **Encryption Key Support (REG4/REG5)**
   - ❌ **Original:** Encryption Keys nicht unterstützt (mit FIXME kommentiert)
   - ✅ **Verbessert:**
     - Vollständige REG4/REG5 Unterstützung
     - `crypt_h` und `crypt_l` Parameter in `__init__`
     - `set_encryption_key()` Methode hinzugefügt
     - Encryption wird in `encode_config()` und `decode_config()` verarbeitet

5. **Modell-Varianten Unterstützung**
   - ❌ **Original:** Nur eine Power-Tabelle für alle Modelle
   - ✅ **Verbessert:** Unterstützung für verschiedene Modellvarianten:
     - **T20/T22:** 22/17/13/10 dBm
     - **T27:** 27/24/21/18 dBm
     - **T30:** 30/27/24/21 dBm
   - Automatische Erkennung basierend auf Modellnamen

6. **CPython Kompatibilität**
   - ❌ **Original:** Nur für MicroPython (ESP32, RP2040)
   - ✅ **Verbessert:**
     - Funktioniert mit Standard Python 3
     - Verwendet `pyserial` statt `machine.UART`
     - Kompatibel mit Linux, macOS, Windows

7. **Bessere Validierung**
   - ✅ **Neu:** `_validate_config()` Methode prüft alle Parameter
   - ✅ **Neu:** Fehlermeldungen für ungültige Konfigurationen
   - ✅ **Neu:** Type hints für bessere Code-Qualität

8. **Verbesserte Dokumentation**
   - ✅ **Neu:** Vollständige Docstrings für alle Methoden
   - ✅ **Neu:** Type hints (Python 3.6+)
   - ✅ **Neu:** Detaillierte Kommentare basierend auf offizieller Doku

9. **Command-Line Interface**
   - ✅ **Neu:** Vollständiges CLI mit argparse
   - ✅ **Neu:** `--read` zum Lesen der aktuellen Konfiguration
   - ✅ **Neu:** `--write` zum Schreiben neuer Konfiguration
   - ✅ **Neu:** `--debug` für detaillierte Ausgaben

### 📝 Register-Mapping nach offizieller Doku

Basierend auf [E22_REGISTER_REFERENCE.md](E22_REGISTER_REFERENCE.md):

#### REG0 (UART & Air Data Rate)
```python
# Bits 7-5: UART Baudrate (000=1200 ... 111=115200)
# Bits 4-3: Parity (00=8N1, 01=8O1, 10=8E1)
# Bits 2-0: Air Data Rate (000=0.3k ... 111=62.5k)
```

#### REG1 (Power & Packet)
```python
# Bits 7-6: Sub-Packet (00=240B, 01=128B, 10=64B, 11=32B)
# Bit  5:   Ambient Noise Enable (0=AUS, 1=EIN)
# Bits 4-2: Reserviert (000)
# Bits 1-0: TX Power (00=MAX, 11=MIN) ⚡ WICHTIG!
```

#### REG2 (Channel)
```python
# Kanal 0-80 (manche Modelle 0-83)
```

#### REG3 (Transmission Modi)
```python
# Bit  7:   RSSI Byte Enable
# Bit  6:   Transmission Mode (0=Transparent, 1=Fixed)
# Bit  5:   Repeater Enable
# Bit  4:   LBT Enable
# Bit  3:   WOR Control (0=Receiver, 1=Transmitter)
# Bits 2-0: WOR Wake-up Period (000=500ms ... 111=4000ms)
```

#### REG4 & REG5 (Encryption) - NEU!
```python
# REG4: Encryption Key High Byte
# REG5: Encryption Key Low Byte
```

### 🔧 Verwendung

#### Grundlegende Verwendung
```python
from e22_improved import EbyteE22

# E22 Modul erstellen
e22 = EbyteE22(
    port='/dev/ttyUSB0',
    model='900T22D',
    address=0x000A,
    channel=23,
    tx_power='22dBm',
    repeater=True,
    lbt=True,
    debug=True
)

# Verbinden
e22.connect()

# Konfiguration anzeigen
e22.show_config()

# Konfiguration schreiben
e22.write_config(save=True)

# Konfiguration lesen
config = e22.read_config()

# Encryption Key setzen
e22.set_encryption_key(0x12, 0x34)

# Trennen
e22.disconnect()
```

#### Command-Line Verwendung
```bash
# Aktuelle Konfiguration lesen
./e22_improved.py --port /dev/ttyUSB0 --read

# Neue Konfiguration schreiben
./e22_improved.py --port /dev/ttyUSB0 --write \
    --address 0x000A \
    --channel 23 \
    --power 22dBm \
    --air-rate 2.4k \
    --repeater \
    --lbt \
    --debug

# T30 Modell mit maximaler Power
./e22_improved.py --port /dev/ttyUSB0 --model 900T30S \
    --write --power 30dBm --channel 10
```

### 📊 Vergleich: Original vs. Verbessert

| Feature | Original | Verbessert |
|---------|----------|------------|
| Platform | MicroPython | CPython + MicroPython |
| Sub-Packet Config | ❌ Hardcoded | ✅ Konfigurierbar |
| Encryption Keys | ❌ Nicht unterstützt | ✅ Vollständig |
| Modellvarianten | ❌ Eine Power-Tabelle | ✅ T20/T22/T27/T30 |
| Validierung | ⚠️ Minimal | ✅ Vollständig |
| Type Hints | ❌ Keine | ✅ Vollständig |
| CLI | ⚠️ Basic | ✅ Vollständig |
| Dokumentation | ⚠️ Kommentare | ✅ Docstrings + Doku |
| Bug: LBT Typo | ❌ 'disabe' | ✅ 'enable' |
| Bug: subpckt init | ❌ Fehlt | ✅ Vorhanden |

### 🔗 Quellen

- **Original Script:** https://github.com/matthias-bs/loraE22
- **Offizielle Ebyte Doku:**
  - https://www.cdebyte.com/ (E22 Datasheets)
  - https://www.fr-ebyte.com/Uploadfiles/Files/2024-1-9/2024191548299095.pdf
- **Register-Referenz:** [E22_REGISTER_REFERENCE.md](E22_REGISTER_REFERENCE.md)

### 🙏 Credits

- **Original Author:** Matthias Prinke & Heinz-Bernd Eggenstein
- **Improvements:** Basierend auf offizieller Ebyte E22 Dokumentation
- **License:** GNU GPL v3 (wie Original)

---

*Erstellt: 2026-01-13*
*Basierend auf matthias-bs/loraE22 mit offizieller Ebyte-Dokumentation*
