# LoRa Repeater Deployment Guide - Berggipfel Installation

## Systemarchitektur mit Berggipfel-Repeater

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Berggipfel Repeater (1500m ü.NN)                   │
│                                                                               │
│  ┌──────────────────┐          ┌──────────────────┐                         │
│  │  Ebyte E22 LoRa  │ ◄────►   │ Dragino Gateway  │ ◄─── WireGuard ───►     │
│  │   868.1 MHz      │          │  (10.0.0.1)      │                         │
│  └──────────────────┘          └──────────────────┘                         │
│           │                             │                                    │
│           │ LoRa Broadcast              │ UDP/MQTT                          │
│           ▼                             ▼                                    │
└───────────┼─────────────────────────────┼────────────────────────────────────┘
            │                             │
            │                             │ WireGuard Tunnel (~130ms)
            │                             │
            │                             ▼
            │                    ┌─────────────────┐
            │                    │   heissa.de     │
            │                    │   Kansas, USA   │
            │                    │   MQTT Broker   │
            │                    │   lorarep.py    │
            │                    └─────────────────┘
            │
            │ LoRa Coverage (Radius abhängig von SF und Gelände)
            │
    ┌───────┴────────┬─────────┬─────────┬─────────┐
    ▼                ▼         ▼         ▼         ▼
┌────────┐      ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ E22 #1 │      │ E22 #2 │ │ E22 #3 │ │ E22 #4 │ │ E22 #N │
│ Tal A  │      │ Tal B  │ │ Stadt  │ │ Dorf   │ │ Remote │
└────────┘      └────────┘ └────────┘ └────────┘ └────────┘
 ~600m ü.NN     ~700m      ~500m      ~800m      ~1200m
```

## Reichweiten-Berechnung

### Line-of-Sight (LoS) Berechnung

**Formel für Radio Horizon:**
```
d = 3.57 × (√h1 + √h2)
```
wobei:
- d = Distanz in km
- h1 = Höhe Antenne 1 in Metern
- h2 = Höhe Antenne 2 in Metern

**Beispiel: Repeater auf 1500m, Endgerät auf 600m**
```
Höhendifferenz Repeater: 1500m
Höhendifferenz Endgerät: 600m (im Tal)
Antennenhöhe Repeater: 1500 + 3m (Mast) = 1503m
Antennenhöhe Endgerät: 600 + 1.5m (Handheld) = 601.5m

d = 3.57 × (√1503 + √601.5)
d = 3.57 × (38.77 + 24.52)
d = 3.57 × 63.29
d ≈ 226 km (theoretischer Radio Horizon)
```

### Realistische Reichweiten mit E22 Module

**Fresnel Zone Clearance beachten!** Mindestens 60% der ersten Fresnel-Zone muss frei sein.

#### SF12 (Long Range Mode)
- **Flachland/Tal-zu-Berg**: 15-25 km
- **Berg-zu-Berg (LoS)**: 30-50 km
- **Mit Hindernissen**: 5-15 km

#### SF7 (Medium Range Mode)
- **Flachland/Tal-zu-Berg**: 5-10 km
- **Berg-zu-Berg (LoS)**: 15-25 km
- **Mit Hindernissen**: 2-5 km

### Erwartete Coverage in deinem Szenario

**Repeater-Standort:** 1500m ü.NN, 5km von Basis
**Basis-Standort:** ~500-700m ü.NN (angenommen)

| Zielgebiet | Höhe | Entfernung | SF7 | SF12 | Bemerkung |
|------------|------|------------|-----|------|-----------|
| Deine Basis | 600m | 5 km | ✅ Gut | ✅ Exzellent | Direkte LoS |
| Nachbartal 1 | 700m | 8 km | ⚠️ Grenzwertig | ✅ Gut | Teilweise LoS |
| Nachbartal 2 | 800m | 12 km | ❌ Schwierig | ✅ Möglich | Bergkamm dazwischen |
| Nächste Stadt | 500m | 15 km | ❌ Kaum | ⚠️ Grenzwertig | Mehrere Hindernisse |
| Alpine Hütte | 1400m | 20 km | ⚠️ Möglich | ✅ Gut | Berg-zu-Berg LoS |

## Hardware-Empfehlungen für Berggipfel

### LoRa Repeater Hardware

**Option 1: Ebyte E22 + Dragino Gateway (wie geplant)**
- ✅ ChirpStack MQTT Integration vorhanden
- ✅ WireGuard-fähig
- ✅ Bereits in deinem System
- ❌ Benötigt kontinuierliche Stromversorgung
- ❌ Internet-Konnektivität erforderlich

**Option 2: Standalone LoRa Repeater (für Infrastructure-less)**
- Basierend auf ESP32 + Ebyte E22
- rf95modem Firmware (aus Paper)
- Batterie + Solar
- Kein Internet benötigt

### Stromlösung für 1500m Höhe

#### Solar + Batterie System
```
Komponenten:
├─ Solar Panel: 100W (min), besser 150-200W
├─ Laderegler: MPPT 20A
├─ Batterie: 12V 100Ah LiFePO4 (1280Wh)
├─ Spannungswandler: 12V → 5V/3A (für Gateway)
└─ Backup: 12V → 5V/5A (für E22 + Raspberry Pi)

Energiebedarf pro Tag (SF7 Dauerbetrieb):
- Dragino Gateway: ~5W × 24h = 120Wh
- E22 Modul: ~0.4W × 24h = 9.6Wh
- Raspberry Pi (optional): ~2.5W × 24h = 60Wh
─────────────────────────────────────────
Total: ~190Wh/Tag

Solar-Ertrag auf 1500m (Alpen):
- Sommer: 800-1000Wh/Tag (100W Panel)
- Winter: 200-400Wh/Tag (100W Panel)
→ 150W Panel empfohlen für Winter-Sicherheit!
```

#### Netzstrom (falls verfügbar)
- Gipfel-Hütte mit Stromanschluss
- Wetterstation-Infrastruktur nutzen
- Mobilfunkmast-Infrastruktur (Genehmigung!)

### Antennen-Setup

**Höhengewinn optimal nutzen:**

#### Option A: Omnidirektional (360° Coverage)
```
Antenne: Halb-Wellen-Dipol 868MHz
Gewinn: +3 dBi (wie Paper verwendet)
Montage: Vertikal, 3m Mast
Vorteil: Rundum-Abdeckung
Nachteil: Geringere Reichweite pro Richtung
```

#### Option B: Sektoral (gerichtete Coverage)
```
3× Antennen zu je 120° Sektor
Gewinn: +8-10 dBi pro Sektor
Montage: 3× E22 Module, 3× Richtantennen
Vorteil: Maximale Reichweite (40-60km möglich)
Nachteil: Komplexer, teurer, mehr Stromverbrauch
```

#### Option C: Hybrid
```
1× Omnidirektional für Nahbereich (0-10km)
1× Richtantenne für Haupttal (bis 40km)
2× E22 Module
```

**Empfehlung für Start: Option A (Omni +3dBi)**

### Wetterschutz

**Kritisch auf 1500m Höhe!**

```
Gehäuse-Anforderungen:
├─ IP67 (wasserdicht, staubdicht)
├─ UV-beständig
├─ Temperaturbereich: -30°C bis +60°C
├─ Blitzschutz: Überspannungsableiter
├─ Kabeldurchführungen: PG-Verschraubungen
└─ Belüftung: Gore-Tex Membrane gegen Kondensation

Empfohlene Gehäuse:
- Fibox ARCA IEC (Polycarbonat)
- Bopla Bocube (Aluminium + Dichtungen)
- Selbstbau: Pelican Case 1200 + Modifikationen
```

## Installations-Checkliste

### Vor der Installation

- [ ] Line-of-Sight Analyse (Google Earth, QGIS)
- [ ] Genehmigungen einholen (Grundstückseigentümer, Behörden)
- [ ] Wetter-Fenster planen (Sommer, wenig Wind)
- [ ] Backup-Plan bei Hardware-Ausfall
- [ ] Montage-Material besorgen (Edelstahl-Schrauben, Rohrschellen)

### Montage

- [ ] Mast installieren (min. 3m Höhe, verzinkter Stahl)
- [ ] Erdung/Blitzschutz (Potentialausgleich)
- [ ] Antennen-Montage (SMA-Kabel max. 3m wegen Dämpfung)
- [ ] Gehäuse-Befestigung (windgeschützt, Süd-Ausrichtung für Solar)
- [ ] Kabel-Zugentlastung

### Inbetriebnahme

- [ ] E22 konfigurieren (Frequenz, SF, Power)
```bash
./e22.py --port /dev/ttyUSB0 \
  --channel 18 \         # 868.1 MHz
  --air-rate 2.4k \      # SF7 äquivalent
  --power 27dBm \        # Maximum für Reichweite
  --rssi-enable 1
```

- [ ] Dragino Gateway konfigurieren
- [ ] WireGuard Tunnel testen
- [ ] MQTT Verbindung zu heissa.de prüfen
- [ ] Reichweiten-Test vom Tal aus

### Test-Protokoll

**Tag 1: Line-of-Sight Test**
```
Test-Setup:
- Sender: Deine Basis (600m)
- Repeater: Berg (1500m)
- Spreading Factor: SF12, dann SF7
- Payload: GPS-Position alle 15s

Messungen:
- RSSI-Werte dokumentieren
- SNR notieren
- Packet Loss Rate berechnen
- Verschiedene Standorte im Tal testen
```

**Tag 2: Non-Line-of-Sight Test**
```
- Hinter Hügeln
- In Wäldern
- In Gebäuden
- Bei verschiedenen Wetterbedingungen
```

## LoRa Repeater Modi

### Modus 1: Transparent Repeater (aktueller Plan)
```python
# Auf heissa.de läuft lorarep.py
# Empfängt von Dragino Gateway via MQTT
# Sendet Echo zurück auf gleicher Frequenz
```

**Vorteile:**
- ✅ Einfache Implementierung (bereits vorhanden)
- ✅ Logging/Monitoring zentral
- ✅ Alle Nachrichten werden archiviert

**Nachteile:**
- ❌ 260ms+ Latenz durch WireGuard
- ❌ Internet-Abhängigkeit
- ❌ Single Point of Failure

### Modus 2: Lokaler Repeater (rf95modem-basiert)
```python
# ESP32 mit 2× E22 Modulen
# Empfängt auf 868.1 MHz (SF12)
# Sendet auf 868.3 MHz (SF7) → Frequenzshift vermeidet Kollision
# Keine Internet-Verbindung nötig
```

**Vorteile:**
- ✅ <100ms Latenz
- ✅ Infrastructure-less
- ✅ Batterie-betrieben möglich

**Nachteile:**
- ❌ Kein zentrales Logging
- ❌ Frequenzkoordination nötig
- ❌ Mehr Hardware-Komplexität

### Modus 3: Hybrid (empfohlen!)
```
┌─────────────────────────────────────┐
│     Berggipfel-Repeater (1500m)     │
│                                     │
│  ┌──────────────┐  ┌──────────────┐│
│  │ E22 #1       │  │ Dragino GW   ││
│  │ 868.1 MHz    │  │ → heissa.de  ││
│  │ Lokal-Repeat │  │ (Backup)     ││
│  └──────────────┘  └──────────────┘│
└─────────────────────────────────────┘
        │                    │
        │                    └─ Internet (wenn verfügbar)
        │
        └─ LoRa Broadcast (immer aktiv)
```

**Implementierung:**
1. rf95modem auf ESP32 für lokales Echo (primär)
2. Dragino Gateway für Internet-Anbindung (sekundär)
3. Bei Internet-Ausfall: Weiter lokales Repeat
4. Bei Internet-Verfügbarkeit: Zusätzlich Cloud-Logging

## Frequenz-Plan für Repeater-Betrieb

**Problem:** Repeater darf nicht eigene Aussendung empfangen (Feedback-Loop!)

**Lösung 1: Time-Division**
```
Slot 1 (0-500ms):   Repeater empfängt (RX)
Slot 2 (500-1000ms): Repeater sendet (TX)
Slot 3 (1000-1500ms): Repeater empfängt (RX)
...
```

**Lösung 2: Frequency-Division (empfohlen)**
```
Uplink:   868.1 MHz (Endgeräte → Repeater)
Downlink: 868.3 MHz (Repeater → Endgeräte)

Oder:
Uplink:   868.1 MHz SF12 (Long Range)
Downlink: 868.1 MHz SF7  (Fast, nach Delay)
```

**Lösung 3: Code-Division**
```
Präambel-Erkennung:
- Endgeräte senden mit Sync Word 0x12
- Repeater sendet mit Sync Word 0x34
- E22 filtert automatisch
```

## Monitoring & Wartung

### Remote-Monitoring Setup

**Node-RED Dashboard auf heissa.de:**
```javascript
// MQTT Subscribe: gateway/+/event/up
// Visualisierung:
- Anzahl empfangener Pakete pro Stunde
- RSSI/SNR Heatmap
- Repeater Uptime
- Batterie-Spannung (falls Solar)
- Temperatur im Gehäuse
```

**Alerts einrichten:**
```python
# lorarep.py erweitern:
if last_packet_time > 3600:  # 1 Stunde keine Pakete
    send_email_alert("Repeater offline?")

if rssi < -140:
    log_warning("Schwaches Signal")
```

### Wartungs-Intervalle

**Monatlich (Remote):**
- [ ] RSSI-Statistiken prüfen
- [ ] Packet Loss Rate analysieren
- [ ] System-Logs durchsehen
- [ ] Batterie-Status (wenn Solar)

**Vierteljährlich (Vor-Ort):**
- [ ] Antennen-Befestigung prüfen
- [ ] Gehäuse-Dichtungen checken
- [ ] Kabel-Verbindungen nachziehen
- [ ] Solar-Panel reinigen

**Jährlich:**
- [ ] Komplette Hardware-Inspektion
- [ ] Batterie-Kapazität messen
- [ ] Korrosion prüfen (Salzluft, Feuchtigkeit)
- [ ] Firmware-Updates

## Kosten-Kalkulation

### Hardware
```
Ebyte E22 Modul (400M30S):        ~25 EUR
oder E22 USB (direkt):            ~35 EUR
Dragino LPS8 Gateway:            ~200 EUR
oder DIY (ESP32 + E22):           ~50 EUR

Antenne +3dBi omnidirektional:    ~20 EUR
5m LMR-400 Kabel:                 ~30 EUR
Blitzschutz:                      ~40 EUR

Solar Panel 150W:                ~150 EUR
MPPT Laderegler:                  ~60 EUR
LiFePO4 Batterie 100Ah:          ~300 EUR

IP67 Gehäuse (Fibox ARCA):       ~120 EUR
3m Edelstahl-Mast:                ~80 EUR
Montage-Material:                 ~50 EUR
─────────────────────────────────────
Gesamt (Solar-Setup):          ~1,100 EUR
Gesamt (Netz-Setup):             ~600 EUR
```

### Laufende Kosten
```
Stromkosten (bei Netz): ~5 EUR/Monat
Internet (4G/LTE): ~15 EUR/Monat (optional)
Wartung: ~100 EUR/Jahr
```

## Rechtliche Aspekte

### ISM-Band Regulierung (EU)
- ✅ 868 MHz: Lizenzfrei (SRD860)
- ⚠️ Max. Sendeleistung: 25 mW ERP (14 dBm)
- ⚠️ Duty Cycle: Max. 1% (oder 10% auf bestimmten Subkanälen)

**E22 mit 27 dBm (500mW) überschreitet Limit!**
→ Entweder drosseln auf 14 dBm oder Amateurfunk-Lizenz!

### Amateurfunk Option
```
Voraussetzung: Amateurfunk-Lizenz (Klasse E/A)
Frequenzen: 433 MHz (70cm Band)
Sendeleistung: Bis 750W (für Klasse A)
Vorteil: Höhere Leistung erlaubt
Nachteil: Lizenzpflicht, nur für Funkamateure
```

### Standort-Genehmigungen
- Grundstückseigentümer-Zustimmung
- Bei Naturschutzgebiet: Behörden-Genehmigung
- Bei Mobilfunkmasten: Betreiber kontaktieren
- Bei staatlichen Gebäuden: Offizielles Genehmigungsverfahren

## Weiterführende Optimierungen

### Mesh-Netzwerk
```
Repeater 1 (1500m) ←──┐
                       ├──→ Repeater 2 (1200m)
Repeater 3 (1100m) ←──┘
```
- Redundanz bei Ausfall
- Größere Coverage durch Multi-Hop
- rf95modem + DTN7 (aus Paper)

### Adaptive Data Rate (ADR)
```python
# E22 automatisch SF anpassen basierend auf RSSI
if rssi > -100:
    use_sf7()  # Schnell, kurze Airtime
elif rssi > -120:
    use_sf10()  # Mittel
else:
    use_sf12()  # Maximum Reichweite
```

### Richtfunk-Link zu heissa.de
```
Statt WireGuard über Internet:
→ Richtfunk 5 GHz zu nächstem Internet-POP
→ Dedizierte Leitung
→ Geringere Latenz (~20-50ms)
```

## Referenzen aus Paper

**Reichweiten-Benchmarks (Höchst et al. 2020):**
- Urban SF7: 1.09 km
- Urban SF12: 2.89 km
- Rural SF7: 1.31 km
- Rural SF12: 1.64 km

**Deine erwartete Reichweite (1500m Höhe):**
- SF7: 5-10 km (Tal), 15-25 km (Berg-zu-Berg)
- SF12: 15-25 km (Tal), 30-50 km (Berg-zu-Berg)

→ **10-20× Verbesserung durch Höhengewinn!**

## Kontakt & Support

Bei Fragen zur Installation:
- LoRa Community Forum: https://forum.lora-alliance.org/
- rf95modem GitHub: https://github.com/gh0st42/rf95modem/
- E22 Dokumentation: Ebyte Website
