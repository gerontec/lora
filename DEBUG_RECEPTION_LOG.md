# Dragino LoRa Reception Debug Log

## Test Setup

**Datum:** 2026-01-09
**Test-Tool:** `test_loragw_hal_rx -r 1250 -a 867.1 -b 868.5 -k 0`
**Gateway:** Dragino LPS8 (dragino-27e318)
**Sender:** E22 USB Module
**Ziel:** Verbindungstest zwischen E22 und Dragino auf 868.1 MHz

---

## Gateway Konfiguration

```
rf_chain 0: 867.1 MHz
rf_chain 1: 868.5 MHz

Multi-Channel IF Configuration:
├─ if_chain 0: 867.1 - 0.4 = 866.7 MHz
├─ if_chain 1: 867.1 - 0.2 = 866.9 MHz
├─ if_chain 2: 867.1 + 0.0 = 867.1 MHz
├─ if_chain 3: 868.5 - 0.4 = 868.1 MHz ✅ TARGET
├─ if_chain 4: 868.5 - 0.2 = 868.3 MHz
├─ if_chain 5: 868.5 + 0.0 = 868.5 MHz
├─ if_chain 6: 868.5 + 0.2 = 868.7 MHz
└─ if_chain 7: 868.5 + 0.4 = 868.9 MHz
```

---

## E22 Konfiguration

### Initiale Konfiguration (Fehlerhaft)
```
Channel: 17
Frequency: 867.1 MHz (850.125 + 17 × 1.0)
Air Rate: 1.2k
TX Power: 13 dBm
Status: ❌ Falsche Frequenz
```

### Korrigierte Konfiguration
```bash
./e22.py --port /dev/ttyUSB0 --channel 18 --power 22dBm
```

```
Channel: 18
Frequency: 868.1 MHz (850.125 + 18 × 1.0)
Air Rate: 1.2k
TX Power: 22 dBm
Status: ✅ Korrekte Frequenz
```

---

## Empfangene Debug-Nachrichten

### Paket #1 - Alte Frequenz (867.1 MHz)

**Empfangen während Channel 17 Konfiguration:**

```
ERROR: wrong coding rate (0) - timestamp_counter_correction
lgw_receive:1323: INFO: RSSI temperature offset applied: 0.000 dB (current temperature 26.9 C)
lgw_receive:1326: INFO: nb pkt found:1 left:0

----- LoRa packet -----
  count_us:   88877234
  size:       0
  chan:       5
  status:     0x01
  datr:       7
  codr:       0
  rf_chain    0
  freq_hz     867100000
  snr_avg:    1.2
  rssi_chan:  106.0
  rssi_sig:   112.0
  crc:        0x0000

Received 1 packets (total:0)
```

**Analyse:**
| Parameter | Wert | Bedeutung |
|-----------|------|-----------|
| `freq_hz` | 867100000 | 867.1 MHz - **Falsche Frequenz** |
| `chan` | 5 | IF Channel 5 (rf_chain 1) |
| `rf_chain` | 0 | RF Chain 0 verwendet (867.1 MHz) |
| `size` | 0 | **Keine Payload** - Modulation Mismatch |
| `datr` | 7 | Data Rate 7 (SF7) ✅ |
| `codr` | 0 | **Coding Rate 0 = ERROR** ❌ |
| `snr_avg` | 1.2 | Signal-to-Noise Ratio: 1.2 dB (schwach) |
| `rssi_chan` | 106.0 | Channel RSSI (sehr ungewöhnlich hoch) |
| `rssi_sig` | 112.0 | Signal RSSI (sehr ungewöhnlich hoch) |
| `status` | 0x01 | CRC_OK Flag gesetzt |

**Probleme:**
- ❌ `codr: 0` - Coding Rate konnte nicht dekodiert werden
- ❌ `size: 0` - Keine Nutzdaten empfangen
- ⚠️ RSSI Werte unrealistisch hoch (typisch: -120 bis -30 dBm)

---

### Paket #2 - Korrekte Frequenz (868.1 MHz)

**Empfangen nach Channel 18 Konfiguration:**

```
WARNING: Not connect I2C Temperature Device, Return Virtual Temperature!
ERROR: wrong coding rate (0) - timestamp_counter_correction
lgw_receive:1323: INFO: RSSI temperature offset applied: 0.000 dB (current temperature 26.9 C)
lgw_receive:1326: INFO: nb pkt found:1 left:0

----- LoRa packet -----
  count_us:   292809056
  size:       0
  chan:       0
  status:     0x01
  datr:       7
  codr:       0
  rf_chain    1
  freq_hz     868100000
  snr_avg:    0.2
  rssi_chan:  124.0
  rssi_sig:   124.0
  crc:        0x0000

Received 1 packets (total:0)
```

**Analyse:**
| Parameter | Wert | Bedeutung |
|-----------|------|-----------|
| `freq_hz` | 868100000 | 868.1 MHz - **✅ Korrekte Frequenz!** |
| `chan` | 0 | IF Channel 0 |
| `rf_chain` | 1 | RF Chain 1 (868.5 MHz base) |
| `size` | 0 | **Keine Payload** - Modulation Mismatch |
| `datr` | 7 | Data Rate 7 (SF7) ✅ |
| `codr` | 0 | **Coding Rate 0 = ERROR** ❌ |
| `snr_avg` | 0.2 | Signal-to-Noise Ratio: 0.2 dB (sehr schwach) |
| `rssi_chan` | 124.0 | Channel RSSI (unrealistisch) |
| `rssi_sig` | 124.0 | Signal RSSI (unrealistisch) |
| `status` | 0x01 | CRC_OK Flag gesetzt |

**Verbesserung:**
- ✅ Frequenz 868.1 MHz korrekt!
- ✅ IF Channel 0 triggert (sollte eigentlich chan 3 sein, aber empfängt)
- ❌ Immer noch `codr: 0` und `size: 0`

---

## Problem-Analyse

### 1. Coding Rate Mismatch ❌

**Symptom:** `ERROR: wrong coding rate (0)`

**Ursache:** E22 und Dragino Gateway verwenden unterschiedliche Coding Rates.

**E22 Default:**
- Coding Rate wird über "Air Rate" Parameter gesteuert
- Air Rate 1.2k entspricht nicht direkt einer CR

**Dragino Gateway:**
- Erwartet Standard Coding Rates: CR 4/5, 4/6, 4/7, oder 4/8
- Kann CR 0 nicht dekodieren

**Lösung:**
- E22 muss explizit Coding Rate konfigurieren
- Oder: Dragino Gateway im "permissive mode" betreiben

### 2. Fehlende Payload (size: 0)

**Symptom:** `size: 0` trotz Transmission

**Mögliche Ursachen:**
1. **Bandwidth Mismatch:** E22 BW ≠ Gateway BW
2. **Preamble Length:** Unterschiedliche Preamble
3. **Sync Word:** Unterschiedliche LoRa Sync Words
4. **IQ Inversion:** Möglicherweise invertiert

**E22 Parameter prüfen:**
```bash
./e22.py --port /dev/ttyUSB0
```

Erwartete Parameter:
- Bandwidth: 125 kHz
- Coding Rate: 4/5
- Preamble: 8 symbols (Standard)
- Sync Word: 0x12 (LoRaWAN public) oder 0x34 (private)

### 3. RSSI Werte unrealistisch hoch

**Symptom:** RSSI 106.0 / 112.0 / 124.0 dBm

**Normale RSSI-Range:** -120 dBm (schwach) bis -30 dBm (sehr stark)

**Mögliche Ursachen:**
- RSSI wird als unsigned int interpretiert
- Temperatur-Kompensation fehlerhaft
- Hardware-Kalibrierung Problem

**Hinweis:** Dies ist ein Anzeige-Problem, beeinflusst Empfang nicht.

---

## Erfolgs-Kriterien

### Gateway empfängt Signale ✅
- Beide Frequenzen (867.1 und 868.1 MHz) wurden detektiert
- SNR positiv (Signal erkennbar)
- Status 0x01 (CRC_OK)

### Payload dekodierung fehlschlägt ❌
- `size: 0` - Keine Nutzdaten
- `codr: 0` - Coding Rate nicht erkannt

---

## Nächste Schritte

### 1. E22 Air Rate / Coding Rate anpassen

Die E22 "Air Rate" Parameter müssen auf Dragino LoRaWAN Standard abgestimmt werden:

| Air Rate | SF | BW | CR |
|----------|----|----|-----|
| 0.3k | SF11 | 125 | 4/8 |
| 1.2k | SF9 | 125 | 4/7 |
| 2.4k | SF7 | 125 | 4/5 |
| 4.8k | SF7 | 250 | 4/5 |
| 9.6k | SF7 | 500 | 4/5 |

**Empfohlene Konfiguration:**
```bash
./e22.py --port /dev/ttyUSB0 --channel 18 --air-rate 2.4k
```

Dies setzt: SF7, BW 125 kHz, CR 4/5 - Standard LoRaWAN EU868.

### 2. Production-Modus testen

Nach Dragino Reboot:

**Auf heissa.de:**
```bash
cd /home/user/lora
python3 lorarep.py
```

**Auf PC:**
```bash
./test_send.py --interval 5
```

**Erwartete MQTT-Nachricht:**
```json
{
  "rxpk": [{
    "tmst": 292809056,
    "chan": 0,
    "rfch": 1,
    "freq": 868.1,
    "stat": 1,
    "modu": "LORA",
    "datr": "SF7BW125",
    "codr": "4/5",
    "lsnr": 0.2,
    "rssi": -124,
    "size": 17,
    "data": "VGVzdCAjMSAxNjoxNzo0NQ=="
  }]
}
```

### 3. Vollständige Parameter-Übereinstimmung prüfen

| Parameter | E22 | Dragino | Status |
|-----------|-----|---------|--------|
| Frequency | 868.1 MHz | 868.1 MHz | ✅ |
| SF | SF7 | SF7 | ✅ |
| Bandwidth | ? | 125 kHz | ⚠️ |
| Coding Rate | ? | 4/5 | ❌ |
| Preamble | ? | 8 | ⚠️ |
| Sync Word | ? | 0x34 | ⚠️ |

---

## Zusammenfassung

### ✅ Erfolge
1. E22 Channel 17→18 korrigiert (867.1→868.1 MHz)
2. Gateway empfängt LoRa-Signale auf korrekter Frequenz
3. Frequenz-Abstimmung erfolgreich

### ❌ Offene Probleme
1. Coding Rate Mismatch verhindert Payload-Dekodierung
2. E22 Air Rate muss auf 2.4k gesetzt werden
3. RSSI Werte unrealistisch (Display-Bug)

### 🎯 Nächster Schritt
```bash
./e22.py --port /dev/ttyUSB0 --channel 18 --air-rate 2.4k
```

Dann reboot Dragino und Production-Test starten.
