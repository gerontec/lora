# LoRa E22/Dragino Kompatibilitäts-Diagnose

## Aktueller Status: KEINE PAKETE EMPFANGEN

### E22-900T Konfiguration
- **Frequenz:** 867.125 MHz (Kanal 17)
- **Air Rate:** 2.4k (vereinfachte Angabe)
- **Bandbreite:** Unbekannt (muss ermittelt werden)
- **Spreading Factor:** Unbekannt (versteckt in "2.4k")
- **Coding Rate:** Unbekannt
- **Transmit Power:** 13 dBm
- **Mode:** Transparent (raw LoRa, NICHT LoRaWAN)

### Dragino Gateway Konfiguration
- **Frequenzen:** chan_multiSF_3 = 867.1 MHz (±25 kHz zum E22) ✓
- **Bandbreite:** 125 kHz
- **Spreading Factor:** SF7-SF12 (all SF)
- **Coding Rate:** Typisch 4/5
- **Radiostream:** Enabled (sollte raw packets erlauben)
- **Gateway Type:** LoRaWAN (SX1302, Semtech protokoll)

## E22 "Air Rate" Bedeutung

Das E22 Datenblatt definiert "Air Rate" als Kombination aus:
- Bandbreite (BW)
- Spreading Factor (SF)
- Forward Error Correction (FEC/Coding Rate)

**Typische E22 "2.4k" Konfiguration:**
- **250 kHz BW + SF7** = ~2.4 kbps ❌ (Gateway hat 125kHz)
- **125 kHz BW + SF8** = ~1.8 kbps (nah an 2.4k, möglich)
- **125 kHz BW + SF7** = ~5.5 kbps (zu schnell)

**PROBLEM:** E22 verwendet möglicherweise 250 kHz Bandbreite, aber Gateway nur 125 kHz!

## Lösungsansätze

### 1. E22 auf 1.2k Air Rate ändern (125kHz BW garantiert)
```bash
./e22.py --channel 17 --air-rate 1.2k
```
Dies sollte 125kHz Bandbreite mit SF9 oder SF10 ergeben.

### 2. Kanal 18 testen (868.125 MHz = näher an 868.1 MHz)
```bash
./e22.py --channel 18 --air-rate 1.2k
```

### 3. FSK Kanal testen (868.8 MHz)
Das Gateway hat einen FSK Kanal bei 868.8 MHz (50kbps).
```bash
# E22 Kanal 18.675 ist nicht möglich, nächster:
./e22.py --channel 19  # 869.125 MHz
```

### 4. Radiostream/Ghost Mode prüfen
Überprüfen ob raw packet capture läuft:
```bash
# Auf Dragino:
ps | grep radio
netstat -an | grep 1760  # Ghost port
```

### 5. LoRaWAN Node simulieren
Statt raw LoRa ein LoRaWAN-Protokoll verwenden (kompliziert, braucht OTAA/ABP setup).

## Nächste Schritte

1. **Air Rate auf 1.2k ändern** (garantiert 125kHz BW)
2. **test_send.py starten** und Dragino logread beobachten
3. **Falls immer noch nichts:** E22 Datenblatt konsultieren für genaue BW/SF Mappings
4. **Alternative:** Zwei E22 Module verwenden (Sender/Empfänger) ohne Gateway
