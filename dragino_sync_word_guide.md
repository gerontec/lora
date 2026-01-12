# Dragino - Sync Word auf 0x12 (Ebyte Standard) ändern

## Was ist das Sync Word?

Das **Sync Word** (auch Network ID oder Preamble) ist ein Identifikations-Byte, das Sender und Empfänger matchen müssen.

**Standard-Werte:**
- **0x34 (52 decimal)** - LoRaWAN Public Network (Standard bei Dragino)
- **0x12 (18 decimal)** - LoRaWAN Private Network / **Ebyte Standard**
- Custom Werte möglich (0x00-0xFF)

**Wichtig:** Sender und Empfänger **müssen** das gleiche Sync Word haben!

---

## Methode 1: Via global_conf.json (Dauerhaft)

### 1. Aktuell konfigurierte Sync Word prüfen:

```bash
ssh root@10.0.0.2 "cat /etc/lora/global_conf.json | grep lorawan_public"
```

**Output:**
```json
"lorawan_public": true,    // Sync Word = 0x34 (LoRaWAN Public)
```

### 2. Auf Ebyte Standard (0x12) ändern:

```bash
ssh root@10.0.0.2 "sed -i 's/\"lorawan_public\": true/\"lorawan_public\": false/' /etc/lora/global_conf.json"
```

**Resultat:**
```json
"lorawan_public": false,   // Sync Word = 0x12 (Private / Ebyte)
```

### 3. Packet Forwarder neu starten:

```bash
ssh root@10.0.0.2 "/etc/init.d/lora-gateway restart"
```

### 4. Prüfen ob aktiv:

```bash
ssh root@10.0.0.2 "logread | grep -i sync | tail -10"
```

---

## Methode 2: Via UCI Konfiguration (OpenWrt)

### 1. UCI Wert prüfen:

```bash
ssh root@10.0.0.2 "uci get lora.@lora[0].lorawan_public"
# Output: 1 (true) oder 0 (false)
```

### 2. Auf Private Network (0x12) setzen:

```bash
ssh root@10.0.0.2 "uci set lora.@lora[0].lorawan_public=0"
ssh root@10.0.0.2 "uci commit lora"
ssh root@10.0.0.2 "/etc/init.d/lora-gateway restart"
```

### 3. Prüfen:

```bash
ssh root@10.0.0.2 "uci show lora.@lora[0].lorawan_public"
# Output: lora.@lora[0].lorawan_public='0'
```

---

## Methode 3: Via test_loragw_hal_rx (Temporär)

Der `test_loragw_hal_rx` Command unterstützt **nicht direkt** das Sync Word als Parameter.

**Workaround:** Modifiziere global_conf.json vor dem Test:

```bash
# Temporär auf 0x12 setzen
ssh root@10.0.0.2 "killall fwd; sed -i 's/\"lorawan_public\": true/\"lorawan_public\": false/' /etc/lora/global_conf.json"

# Test starten
ssh root@10.0.0.2 "test_loragw_hal_rx -r 1250 -a 867.1 -b 867.3 -k 0 -m 0"

# Zurück auf 0x34 (optional)
ssh root@10.0.0.2 "sed -i 's/\"lorawan_public\": false/\"lorawan_public\": true/' /etc/lora/global_conf.json"
```

---

## Methode 4: Via C Code (libloragw API)

Falls du eigenen Code schreibst:

```c
#include "loragw_hal.h"

struct lgw_conf_board_s boardconf;
memset(&boardconf, 0, sizeof boardconf);

// Ebyte Standard: Private Network (0x12)
boardconf.lorawan_public = false;  // false → 0x12, true → 0x34

lgw_board_setconf(&boardconf);
lgw_start();
```

---

## Methode 5: Via Register (Low-Level)

**SX1302 Register:** Sync Word steht in Register `0x0740` (SX1250 LoRa Sync Word)

### Register direkt setzen:

```bash
ssh root@10.0.0.2 "killall fwd; test_loragw_reg -r 1250 -k 0 -w 0x0740 -v 0x12"
```

**Achtung:** Dies ist **temporär** und wird beim nächsten Reset überschrieben!

---

## Verifikation: Sync Word testen

### 1. Script mit neuem Sync Word anpassen:

Erstelle `dragino_remote_monitor_ebyte.py`:

```python
#!/usr/bin/python3
"""
Dragino Monitor mit Ebyte Sync Word (0x12)
"""

DRAGINO_HOST = "10.0.0.2"

# WICHTIG: Setze Sync Word auf Dragino auf 0x12 (Private)
# ssh root@10.0.0.2 "sed -i 's/\"lorawan_public\": true/\"lorawan_public\": false/' /etc/lora/global_conf.json"
# ssh root@10.0.0.2 "/etc/init.d/lora-gateway restart"

import subprocess

cmd = [
    "ssh",
    f"root@{DRAGINO_HOST}",
    "test_loragw_hal_rx -r 1250 -a 867.1 -b 867.3 -k 0 -m 0"
]

print("=" * 60)
print("Dragino Monitor - EBYTE Sync Word 0x12")
print("=" * 60)
print("Wichtig: Stelle sicher dass lorawan_public=false")
print("")

subprocess.run(cmd)
```

### 2. E22 Module auf 0x12 prüfen:

Ebyte E22 Module nutzen **standardmäßig 0x12** (Private Network).

**Kein Änderung nötig am E22!** ✅

---

## Sync Word Referenz

| Wert | Hex | Verwendung | Kompatibilität |
|------|-----|-----------|----------------|
| **52** | 0x34 | LoRaWAN Public | TTN, Helium, Chirpstack |
| **18** | 0x12 | LoRaWAN Private | **Ebyte E22/E90** ✅ |
| 0 | 0x00 | Custom | Eigene Netzwerke |
| 255 | 0xFF | Custom | Test/Debug |

---

## Wichtige Hinweise

⚠️ **Sender und Empfänger müssen gleiches Sync Word haben!**

✅ **Ebyte E22/E90 Standard = 0x12** (Private Network)

✅ **Dragino Standard = 0x34** (Public Network) → **Muss auf 0x12 geändert werden!**

### Typische Fehler:

❌ **Problem:** Dragino empfängt keine Pakete von E22
   **Lösung:** Setze `lorawan_public=false` auf Dragino

❌ **Problem:** Pakete sichtbar aber CRC Error
   **Lösung:** Sync Word falsch → Prüfe 0x12 vs 0x34

---

## Quick Commands

### Setze Dragino auf Ebyte-Kompatibilität (0x12):

```bash
# 1. Sync Word ändern
ssh root@10.0.0.2 "uci set lora.@lora[0].lorawan_public=0 && uci commit lora"

# 2. Neustart
ssh root@10.0.0.2 "/etc/init.d/lora-gateway restart"

# 3. Prüfen
ssh root@10.0.0.2 "logread | grep -i 'lorawan_public\|sync' | tail -5"
```

### Zurück auf LoRaWAN Standard (0x34):

```bash
ssh root@10.0.0.2 "uci set lora.@lora[0].lorawan_public=1 && uci commit lora"
ssh root@10.0.0.2 "/etc/init.d/lora-gateway restart"
```

---

## Zusammenfassung

**Für Ebyte E22/E90 Kompatibilität:**

1. ✅ Setze `lorawan_public=false` auf Dragino
2. ✅ Restart Gateway
3. ✅ Test mit dragino_remote_monitor.py

**Ergebnis:** Dragino empfängt jetzt Ebyte E22/E90 Pakete! 🎉
