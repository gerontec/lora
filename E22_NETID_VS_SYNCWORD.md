# E22 - NetID vs Sync Word (Wichtiger Unterschied!)

## ⚠️ ACHTUNG: NetID ≠ Sync Word!

### NetID (Register C0-C1) - Adressfilter
**Was es ist:**
- Adressfilter auf Protokoll-Ebene
- Funktioniert wie eine "Netzwerk-Gruppe"
- E22 empfängt nur Pakete mit gleicher NetID

**Standard:** 0x0000 (empfängt alle NetIDs)

**Beispiel:**
```
E22 Sender:    NETID=0x0034, ADDR=0xFFFF
E22 Empfänger: NETID=0x0034, ADDR=0xFFFF
→ Kommunikation OK ✅

E22 Sender:    NETID=0x0034
E22 Empfänger: NETID=0x0012
→ Paket wird VERWORFEN ❌ (Filter blockiert)
```

---

### Sync Word (Register C4, Bit 5) - Netzwerk-ID
**Was es ist:**
- LoRa PHY-Layer Parameter (im SX126x Chip)
- **Muss** zwischen Sender/Empfänger matchen
- Wird vom LoRa-Chip selbst geprüft (nicht von E22 Software)

**Werte:**
- **0x12 (18)** = Private Network (E22 Default) ✅
- **0x34 (52)** = LoRaWAN Public Network

**Konfiguration:**
```
Register C4 (Transmission Mode)
Bit 5: LoRaWAN Enable
  0 = Private (Sync Word 0x12) ← E22 DEFAULT
  1 = Public  (Sync Word 0x34) ← LoRaWAN Standard
```

---

## Was passiert bei NetID=0x34?

### Szenario: E22 USB NetID auf 0x34 setzen

```bash
# E22 NetID auf 0x34 setzen (C0-C1 Register)
python3 e22_config.py --netid 0x0034
```

**Resultat:**
- ✅ E22 sendet mit NetID=0x0034 im Paket-Header
- ✅ E22 empfängt NUR Pakete mit NetID=0x0034
- ❌ **Sync Word bleibt 0x12!** (nicht geändert)

**Dragino Empfang:**
- ❌ **Dragino empfängt NICHTS!**
- Grund: Dragino Sync Word = 0x34, E22 Sync Word = 0x12
- **NetID=0x34 hilft NICHT!**

---

## Was du wirklich brauchst

### Option 1: Dragino auf E22 anpassen (Empfohlen)

```bash
# Setze Dragino Sync Word auf 0x12 (E22 Standard)
./dragino_set_ebyte_sync.sh
```

**Vorteil:** E22 braucht keine Änderung ✅

---

### Option 2: E22 auf LoRaWAN anpassen

```bash
# Setze E22 Sync Word auf 0x34 (LoRaWAN Public)
# Register C4, Bit 5 = 1
```

**E22 AT Kommando:**
```
# Lese C4 Register
AT+REG?C4

# Beispiel Output: C4=20 (Binary: 00100000)
# Bit 5 = 0 → Private (0x12)

# Setze Bit 5 = 1
# Neue Wert: 20 | (1<<5) = 20 | 20 = 40 (hex)
AT+REG=C4,60
# 60 = 01100000 (Bit 5+6 gesetzt, typisch für LoRaWAN)
```

**Vorteil:** Dragino Standard (0x34) bleibt ✅
**Nachteil:** Alle E22 Module müssen geändert werden

---

## E22 Register Übersicht

```
╔════════════════════════════════════════════════════════╗
║  E22 Register - NetID vs Sync Word                    ║
╠════════════════════════════════════════════════════════╣
║                                                         ║
║  C0-C1: NETID (Adressfilter)                           ║
║  ├─ Default: 0x0000                                    ║
║  ├─ Funktion: Paketfilter auf Protokoll-Ebene         ║
║  └─ Dragino sieht das: NEIN (PHY-Layer)               ║
║                                                         ║
║  C4: Transmission Mode                                 ║
║  ├─ Bit 5: LoRaWAN Enable                             ║
║  │   0 = Private (Sync 0x12) ← DEFAULT                ║
║  │   1 = Public  (Sync 0x34) ← LoRaWAN                ║
║  └─ Dragino sieht das: JA! (PHY-Layer) ✅             ║
║                                                         ║
╚════════════════════════════════════════════════════════╝
```

---

## Vergleich: Was Dragino sieht

### E22 mit NetID=0x0034, Sync=0x12 (Default)

```
E22 Paket:
┌─────────────────────────────────────┐
│ LoRa PHY Layer                      │
│ ├─ Preamble                         │
│ ├─ Sync Word: 0x12 ← Dragino prüft HIER!
│ └─ Payload:                         │
│    ├─ NetID: 0x0034 ← Dragino sieht das NICHT
│    ├─ ADDR: 0xFFFF                  │
│    └─ Data: ...                     │
└─────────────────────────────────────┘

Dragino Ergebnis: ❌ VERWORFEN
Grund: Sync Word mismatch (0x12 ≠ 0x34)
```

### E22 mit NetID=0x0034, Sync=0x34 (C4 geändert)

```
E22 Paket:
┌─────────────────────────────────────┐
│ LoRa PHY Layer                      │
│ ├─ Preamble                         │
│ ├─ Sync Word: 0x34 ← Dragino Match! ✅
│ └─ Payload:                         │
│    ├─ NetID: 0x0034                 │
│    ├─ ADDR: 0xFFFF                  │
│    └─ Data: ...                     │
└─────────────────────────────────────┘

Dragino Ergebnis: ✅ EMPFANGEN
```

---

## Praktischer Test

### Test 1: NetID ändern (funktioniert NICHT)

```bash
# E22 NetID auf 0x34 setzen
AT+REG=C0,00
AT+REG=C1,34

# Sende Paket
echo "TEST" > /dev/ttyUSB0

# Dragino Monitor
./dragino_remote_monitor.py
# → KEINE Pakete! ❌ (Sync Word mismatch)
```

### Test 2: Sync Word ändern (funktioniert!)

```bash
# E22 Sync Word auf 0x34 (C4 Register)
# Aktueller Wert lesen
AT+REG?C4
# Output: C4=20 (Beispiel)

# Setze Bit 5 (LoRaWAN Enable)
AT+REG=C4,60
# 60 = 0x01100000 (Bit 5+6)

# Sende Paket
echo "TEST" > /dev/ttyUSB0

# Dragino Monitor
./dragino_remote_monitor.py
# → Paket empfangen! ✅
```

---

## E22 C4 Register Bits

```
C4 Register (Transmission Mode):

Bit 7 6 5 4 3 2 1 0
    | | | | | | | |
    | | | | | | | └─ [1:0] Sub-Packet Length
    | | | | | └─────── [2]   RSSI Ambient Noise
    | | | └───────────── [4:3] Reserved
    | | └─────────────────── [5]   LoRaWAN Enable (Sync Word!)
    | └───────────────────────── [6]   Reserved
    └─────────────────────────────── [7]   WOR Enable

Beispiel Werte:
0x20 (00100000) → Bit 5=0 → Private (0x12) ← DEFAULT
0x60 (01100000) → Bit 5=1 → Public  (0x34) ← LoRaWAN
```

---

## Empfehlung

### Für dein Setup (E22 ↔ Dragino):

**Option A: Dragino anpassen (EINFACHER)** ✅
```bash
# Dragino Sync Word auf 0x12 (E22 Standard)
./dragino_set_ebyte_sync.sh

# E22 bleibt auf Default
# → Funktioniert sofort!
```

**Option B: E22 anpassen**
```bash
# Alle E22 Module auf LoRaWAN Sync Word (0x34)
# Jedes Modul einzeln mit AT+REG=C4,60 konfigurieren
# → Aufwändig, aber Dragino bleibt Standard
```

---

## Zusammenfassung

| Parameter | Was es tut | Dragino sieht es? |
|-----------|-----------|-------------------|
| **NetID (C0-C1)** | Adressfilter | ❌ NEIN |
| **Sync Word (C4 Bit5)** | LoRa Netzwerk-ID | ✅ JA! |

**Merksatz:**
- NetID = Briefumschlag-Adresse (E22 intern)
- Sync Word = Postleitzahl (LoRa Chip prüft zuerst!)

**Für E22 ↔ Dragino Kommunikation:**
→ Ändere **Sync Word**, NICHT NetID!
