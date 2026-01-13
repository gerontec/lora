# E22 LoRa Module - Offizielle Register-Referenz

**Quelle:** Ebyte/CDEBYTE E22-Serie Datenblätter und verifizierte Implementierungen

---

## Register-Übersicht (9 Bytes Konfiguration)

| Byte Position | Register | Beschreibung |
|--------------|----------|--------------|
| 0 | ADDH | Adresse High Byte (0x00-0xFF) |
| 1 | ADDL | Adresse Low Byte (0x00-0xFF) |
| 2 | NETID | Netzwerk-ID (0x00-0xFF) |
| 3 | REG0 | UART & Air Data Rate Konfiguration |
| 4 | REG1 | Power & Packet Konfiguration |
| 5 | REG2 | Kanal (0-80 / 0-83 je nach Modell) |
| 6 | REG3 | Transmission Modi & WOR |
| 7 | REG4 | Encryption Key High Byte |
| 8 | REG5 | Encryption Key Low Byte |

---

## REG0 (Byte 3) - UART & Air Data Rate

```
Bit:  7    6    5  |  4    3  |  2    1    0
      [  UART Baud  ] [ Parity ] [ Air Rate  ]
```

### Bits 7-5: UART Baud Rate

| Wert | Binär | Baudrate |
|------|-------|----------|
| 0 | 0b000 | 1200 bps |
| 1 | 0b001 | 2400 bps |
| 2 | 0b010 | 4800 bps |
| **3** | **0b011** | **9600 bps (Standard)** |
| 4 | 0b100 | 19200 bps |
| 5 | 0b101 | 38400 bps |
| 6 | 0b110 | 57600 bps |
| 7 | 0b111 | 115200 bps |

### Bits 4-3: UART Parity

| Wert | Binär | Parity |
|------|-------|--------|
| **0** | **0b00** | **8N1 (Standard)** |
| 1 | 0b01 | 8O1 (Odd Parity) |
| 2 | 0b10 | 8E1 (Even Parity) |
| 3 | 0b11 | 8N1 (wie 0b00) |

### Bits 2-0: Air Data Rate (Funk-Datenrate)

| Wert | Binär | Air Rate | Reichweite |
|------|-------|----------|------------|
| 0 | 0b000 | 0.3 kbps | Maximal |
| 1 | 0b001 | 1.2 kbps | Sehr hoch |
| **2** | **0b010** | **2.4 kbps (Standard)** | **Hoch** |
| 3 | 0b011 | 4.8 kbps | Mittel-Hoch |
| 4 | 0b100 | 9.6 kbps | Mittel |
| 5 | 0b101 | 19.2 kbps | Niedrig |
| 6 | 0b110 | 38.4 kbps | Sehr niedrig |
| 7 | 0b111 | 62.5 kbps | Minimal |

**Hinweis:** Niedrigere Air Data Rate = Höhere Reichweite + Bessere Störfestigkeit

---

## REG1 (Byte 4) - Power & Packet

```
Bit:  7    6  |  5  |  4    3    2  |  1    0
      [ Sub  ] [Noi] [  Reserved  ] [ Power ]
```

### Bits 7-6: Sub-Packet Size

| Wert | Binär | Paketgröße |
|------|-------|------------|
| **0** | **0b00** | **240 Bytes (Standard)** |
| 1 | 0b01 | 128 Bytes |
| 2 | 0b10 | 64 Bytes |
| 3 | 0b11 | 32 Bytes |

### Bit 5: RSSI Ambient Noise Enable

| Wert | Beschreibung |
|------|--------------|
| **0** | **Ambient Noise Messung AUS (Standard)** |
| 1 | Ambient Noise Messung EIN |

### Bits 4-2: Reserviert

Immer `0b000`

### Bits 1-0: Transmitting Power (T20/T27/T30 Module)

**KORRIGIERTE WERTE:**

| Wert | Binär | Power (22dBm Modell) | Power (30dBm Modell) |
|------|-------|----------------------|----------------------|
| **0** | **0b00** | **22 dBm (MAX)** | **30 dBm (MAX)** |
| 1 | 0b01 | 17 dBm | 27 dBm |
| 2 | 0b10 | 13 dBm | 24 dBm |
| 3 | 0b11 | 10 dBm (MIN) | 21 dBm (MIN) |

**Wichtig:** `0b00` ist die **HÖCHSTE** Sendeleistung, `0b11` die **NIEDRIGSTE**!

---

## REG2 (Byte 5) - Channel

Direkter Kanalwert: **0-80** (manche Modelle 0-83)

**Frequenzberechnung** (900MHz Modelle):
```
Frequenz = 850.125 MHz + (Kanal × 1 MHz)
```

**Beispiel:** Kanal 23 → 850.125 + 23 = **873.125 MHz**

---

## REG3 (Byte 6) - Transmission Modi & WOR

```
Bit:  7  |  6  |  5  |  4  |  3  |  2    1    0
     [RSI][Fix][Rep][LBT][WOR] [  WOR Time  ]
```

### Bit 7: RSSI Byte Enable

| Wert | Beschreibung |
|------|--------------|
| **0** | **Kein RSSI-Byte in Empfangsdaten (Standard)** |
| 1 | RSSI-Byte nach jedem Empfangspaket anhängen |

### Bit 6: Transmission Mode

| Wert | Modus | Beschreibung |
|------|-------|--------------|
| **0** | **Transparent (Standard)** | Direkte Datenübertragung |
| 1 | Fixed-Point | Erste 3 Bytes = Zieladresse+Kanal |

### Bit 5: Relay/Repeater Function

| Wert | Beschreibung |
|------|--------------|
| **0** | **Relay AUS (Standard)** |
| 1 | Relay EIN - Modul leitet fremde Pakete weiter |

### Bit 4: LBT (Listen Before Talk)

| Wert | Beschreibung |
|------|--------------|
| **0** | **LBT AUS (Standard)** |
| 1 | LBT EIN - Kanal-Check vor Senden |

### Bit 3: WOR Control

| Wert | Modus |
|------|-------|
| **0** | **WOR Receiver (Standard)** |
| 1 | WOR Transmitter |

### Bits 2-0: WOR Wake-up Period

| Wert | Binär | Wake-up Zeit |
|------|-------|--------------|
| **0** | **0b000** | **500 ms (Standard)** |
| 1 | 0b001 | 1000 ms |
| 2 | 0b010 | 1500 ms |
| 3 | 0b011 | 2000 ms |
| 4 | 0b100 | 2500 ms |
| 5 | 0b101 | 3000 ms |
| 6 | 0b110 | 3500 ms |
| 7 | 0b111 | 4000 ms |

---

## REG4 & REG5 (Bytes 7-8) - Encryption

- **REG4:** Encryption Key High Byte (0x00-0xFF)
- **REG5:** Encryption Key Low Byte (0x00-0xFF)

**Standard:** 0x0000 (keine Verschlüsselung)

---

## Beispiel-Dekodierung: `C00009000A0062E017700000`

### Command Header
- `C0 00 09` = Write Config Command (9 Bytes folgen)

### Konfigurationsdaten: `00 0A 00 62 E0 17 70 00 00`

| Byte | Hex | Binär | Dekodierung |
|------|-----|-------|-------------|
| **ADDH** | 0x00 | - | Adresse High = 0 |
| **ADDL** | 0x0A | - | Adresse Low = 10 |
| **NETID** | 0x00 | - | Netzwerk-ID = 0 |
| **REG0** | 0x62 | 01100010 | UART=9600, Parity=8N1, Air=2.4k |
| **REG1** | 0xE0 | 11100000 | Packet=32B, Noise=ON, Power=22dBm |
| **REG2** | 0x17 | - | Kanal = 23 (873.125 MHz) |
| **REG3** | 0x70 | 01110000 | Fixed+Relay+LBT ON, RSSI Byte OFF |
| **REG4** | 0x00 | - | Crypt High = 0 |
| **REG5** | 0x00 | - | Crypt Low = 0 |

### REG0 (0x62 = 0b01100010) Detail:
- Bits 7-5 = `011` → **9600 bps**
- Bits 4-3 = `00` → **8N1**
- Bits 2-0 = `010` → **2.4 kbps Air Rate**

### REG1 (0xE0 = 0b11100000) Detail:
- Bits 7-6 = `11` → **32 Bytes** Sub-Packet
- Bit 5 = `1` → **Ambient Noise EIN**
- Bits 4-2 = `000` → Reserviert
- Bits 1-0 = `00` → **22 dBm (MAXIMALE Power!)**

### REG3 (0x70 = 0b01110000) Detail:
- Bit 7 = `0` → RSSI Byte **AUS**
- Bit 6 = `1` → **Fixed Transmission**
- Bit 5 = `1` → **Repeater EIN**
- Bit 4 = `1` → **LBT EIN**
- Bit 3 = `0` → WOR Receiver Mode
- Bits 2-0 = `000` → WOR 500ms

---

## Zusammenfassung der Konfiguration

✅ **Modul-Adresse:** 0x000A (10)
✅ **Netzwerk-ID:** 0x00
✅ **Serielle Schnittstelle:** 9600 baud, 8N1
✅ **Funk-Datenrate:** 2.4 kbps (hohe Reichweite)
✅ **Frequenz:** Kanal 23 = 873.125 MHz
✅ **Paketgröße:** 32 Bytes
✅ **Sendeleistung:** **22 dBm (MAXIMUM)** ⚡
✅ **Betriebsmodi:**
  - **Fixed Transmission** - Adressiertes Senden
  - **Repeater aktiv** - Leitet Pakete weiter
  - **LBT aktiv** - Prüft Kanal vor Senden
  - **Ambient Noise Messung** - Umgebungsrauschen messen
  - **RSSI Bytes deaktiviert** - Keine RSSI-Info in Daten

**Einsatzzweck:** Mesh-Netzwerk-Repeater mit **maximaler Sendeleistung** für große Reichweite, optimiert für Mesh-Topologie mit Relay-Funktion und LBT zur Kollisionsvermeidung.

---

## Quellen

- Ebyte/CDEBYTE offizielle E22-Serie Datenblätter
- [E22-900T33S Product Specification](https://www.fr-ebyte.com/Uploadfiles/Files/2024-1-9/2024191548299095.pdf)
- [E22 Official Datasheets](https://www.cdebyte.com/)
- [Verified Python Implementation](https://github.com/matthias-bs/loraE22)

---

*Erstellt: 2026-01-13*
*Basierend auf offizieller Ebyte-Dokumentation*
