# Waveshare Pico-LoRa-SX1262-868M - Complete Setup Guide

## Hardware

**Produkt:** SX1262 LoRa Node Modul für Raspberry Pi Pico
**Chip:** Semtech SX1262
**Frequenz:** 868 MHz (EU868 Band)
**Hersteller:** Waveshare

**Specs:**
- Frequenzbereich: 850-930 MHz
- TX Power: +22 dBm max
- Spreading Factor: SF5-SF12
- Bandwidth: 125/250/500 kHz
- Interface: SPI
- Range: bis 5 km (Line of Sight)

---

## Pin-Mapping

```
Pico Pin → SX1262 Function
──────────────────────────────
GP3      → NSS/CS (Chip Select)
GP10     → SCK (SPI Clock)
GP11     → MOSI (SPI Data Out)
GP12     → MISO (SPI Data In)
GP15     → RST (Reset)
GP2      → BUSY (Status)
GP20     → DIO1 (Interrupt)
3.3V     → VCC
GND      → GND
```

**HAT steckt direkt auf Pico - keine Verkabelung nötig!** ✅

---

## Software Setup

### 1. MicroPython Firmware installieren

**Download:**
https://micropython.org/download/rp2-pico-w/

**Installation:**
1. Halte **BOOTSEL** Button auf Pico W gedrückt
2. Stecke USB-Kabel ein
3. Pico erscheint als **RPI-RP2** USB-Laufwerk
4. Kopiere `.uf2` Datei auf das Laufwerk
5. Pico startet automatisch neu mit MicroPython

**Prüfen:**
```python
# Via Thonny IDE oder Terminal
>>> import sys
>>> sys.version
# Output: MicroPython v1.xx.x on 2024-xx-xx; Raspberry Pi Pico W with RP2040
```

---

### 2. SX1262 Library installieren

**Methode A: Via mip (Internet erforderlich)**

Pico W mit WiFi verbinden:
```python
import network
import time

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('YOUR_SSID', 'YOUR_PASSWORD')

# Warten auf Verbindung
while not wlan.isconnected():
    time.sleep(1)

print('Connected:', wlan.ifconfig())

# Library installieren
import mip
mip.install('github:ehong-tl/micropySX126X')
```

**Methode B: Manuelle Installation**

1. Download von: https://github.com/ehong-tl/micropySX126X
2. Kopiere `sx126x.py` und `sx1262.py` auf Pico (via Thonny)

---

### 3. Crisis Chat installieren

**Kopiere Script auf Pico:**
```bash
# Via Thonny IDE:
# - Öffne pico_sx1262_crisis_chat.py
# - Speichere als "main.py" auf Pico
# - Beim Neustart wird es automatisch gestartet

# Oder via rshell:
pip install rshell
rshell -p /dev/ttyACM0  # Anpassen an deinen Port
> cp pico_sx1262_crisis_chat.py /pyboard/main.py
> repl
```

---

## Konfiguration

### Anpassen in `pico_sx1262_crisis_chat.py`:

```python
# === DEINE EINSTELLUNGEN ===

# Netzwerk-Konfiguration
MY_NETID = 0x0034   # Dein Network ID (muss mit anderen Nodes matchen!)
MY_ADDR = 0x2001    # Deine eindeutige Adresse (für jeden Node anders!)

# LoRa Sync Word
LORA_CONFIG = {
    'syncWord': 0x11,  # 0x11 = Custom
                       # 0x12 = LoRa Private (E22 Default)
                       # 0x34 = LoRaWAN Public
}

# Username
username = "Alice"  # Dein Anzeigename
```

---

## Hardware Test

### Test 1: LoRa Chip Erkennung

```python
from sx1262 import SX1262

# Pin config
sx = SX1262(spi_bus=1, clk=10, mosi=11, miso=12, cs=3, irq=20, rst=15, gpio=2)

# Init
sx.begin(freq=868.1, bw=125.0, sf=9, cr=7, syncWord=0x12, power=14)

print("SX1262 initialized!")
```

**Erfolg:** `SX1262 initialized!`
**Fehler:** Prüfe HAT richtig aufgesteckt?

---

### Test 2: LoRa Senden

```python
from sx1262 import SX1262

sx = SX1262(spi_bus=1, clk=10, mosi=11, miso=12, cs=3, irq=20, rst=15, gpio=2)
sx.begin(freq=868.1, bw=125.0, sf=9, cr=7, syncWord=0x12, power=22)

# Sende Test
sx.send("Hello LoRa!")
print("Sent!")
```

---

### Test 3: LoRa Empfangen

```python
from sx1262 import SX1262
import time

sx = SX1262(spi_bus=1, clk=10, mosi=11, miso=12, cs=3, irq=20, rst=15, gpio=2)
sx.begin(freq=868.1, bw=125.0, sf=9, cr=7, syncWord=0x12, power=22)

def on_receive(data):
    msg = bytes(data).decode()
    print(f"Received: {msg}")

sx.setBlockingCallback(False, on_receive)

print("Listening...")
while True:
    time.sleep(1)
```

---

## Crisis Chat Nutzung

### Quick Start:

```python
from pico_sx1262_crisis_chat import CrisisChatPico

# Erstelle Chat Instance
chat = CrisisChatPico(
    username="Alice",
    netid=0x0034,
    addr=0x2001,
    channel="emergency"
)

# Broadcast senden
chat.send_broadcast("Hilfe benötigt am Berggipfel!")

# Unicast an spezifischen Node
chat.send_to(0x2002, "Bob, kommst du?")

# Höre 60 Sekunden
chat.listen(duration=60)

# Oder interaktiver Modus
chat.interactive()
```

---

### Interaktiver Modus:

```python
>>> chat.interactive()

Crisis Chat - Interactive Mode
NetID: 0034 | Addr: 2001 | User: Alice
==================================================
Commands:
  <text>        - Broadcast message
  @<addr> <msg> - Send to specific address
  /stats        - Show statistics
  /quit         - Exit
==================================================

Alice> Hallo alle zusammen!
[TX→ALL] Hallo alle zusammen!

Alice> @2002 Private Nachricht an Bob
[TX→2002] Private Nachricht an Bob

[emergency][Bob→ALL] Ich komme!

Alice> /stats
TX: 2, RX: 1, Filtered: 0

Alice> /quit
```

---

## Integration mit Dragino Gateway

### Setup:

**1. Pico W (LoRa Sender):**
```python
# Pico mit Sync Word 0x11
chat = CrisisChatPico("Pico1", netid=0x0034, addr=0x2001)
chat.send_broadcast("Test from Pico")
```

**2. Dragino Gateway (LoRa Empfänger):**
```bash
# Setze Dragino auf Sync Word 0x11
ssh root@10.0.0.2
# Siehe: dragino_custom_syncword_guide.md
```

**3. Server (heissa.de):**
```python
# dragino_remote_monitor.py empfängt Pakete
# Parse NetID-Protokoll
```

---

## Multi-Node Setup

### Node 1 (Berggipfel Repeater):
```python
# main.py auf Pico 1
from pico_sx1262_crisis_chat import CrisisChatPico

chat = CrisisChatPico(
    username="Gipfel",
    netid=0x0034,
    addr=0x1000,
    channel="emergency"
)

# Beacon Mode (alle 10 Minuten)
import time
while True:
    chat.send_broadcast("Gipfel-Station aktiv")
    chat.listen(duration=600)  # 10 Minuten hören
```

### Node 2 (Mobile Einheit):
```python
chat = CrisisChatPico(
    username="Mobile1",
    netid=0x0034,
    addr=0x2001,
    channel="emergency"
)

chat.interactive()  # Interaktiver Chat
```

### Node 3 (Koordinationszentrum):
```python
chat = CrisisChatPico(
    username="Zentrale",
    netid=0x0034,
    addr=0x3000,
    channel="emergency"
)

# Multi-Channel Monitor
while True:
    chat.listen(duration=60)
```

---

## Stromverbrauch & Battery Life

### Verbrauch:

| Mode | Strom | Bemerkung |
|------|-------|-----------|
| **TX (22dBm)** | ~120 mA | Während Senden |
| **RX** | ~15 mA | Während Empfang |
| **Sleep** | ~1 mA | Deep Sleep (zu implementieren) |

### Battery Life (mit 18650 - 3000mAh):

**Continuous RX (always on):**
- 15 mA → 3000/15 = **200 Stunden** = ~8 Tage

**Beacon Mode (10min interval, 1min RX):**
- Avg: ~2 mA → 3000/2 = **1500 Stunden** = ~62 Tage

**Emergency Only (sleep + wake on message):**
- Avg: ~0.5 mA → 3000/0.5 = **6000 Stunden** = ~250 Tage

---

## Deep Sleep Mode (TODO)

```python
# Für maximale Battery Life
import machine
import time

def sleep_mode(wake_interval=600):
    """Sleep und wake alle X Sekunden"""

    # Sende Beacon
    chat.send_broadcast("Going to sleep...")

    # Deep Sleep
    machine.deepsleep(wake_interval * 1000)  # ms

# Nach dem Sleep startet Pico neu und führt main.py aus
```

---

## Troubleshooting

### Problem: "No module named 'sx1262'"

**Lösung:**
```python
import mip
mip.install('github:ehong-tl/micropySX126X')
```

---

### Problem: "OSError: [Errno 5] EIO"

**Ursache:** SPI Kommunikation fehlgeschlagen

**Lösung:**
1. Prüfe HAT richtig aufgesteckt
2. Prüfe 3.3V Spannung (nicht 5V!)
3. Pico neu starten

---

### Problem: Keine Pakete empfangen

**Checkliste:**
1. ✅ Sync Word matcht (0x11, 0x12, 0x34)?
2. ✅ Frequenz gleich (868.1 MHz)?
3. ✅ SF/BW gleich (SF9, BW125)?
4. ✅ NetID matcht (0x0034)?
5. ✅ Antenne angeschlossen?

---

### Problem: Range zu kurz

**Verbesserungen:**
1. **Höhere TX Power:** `power=22` (max)
2. **Höherer SF:** `sf=12` (mehr Range, langsamer)
3. **Bessere Antenne:** 868 MHz tuned Antenne
4. **Line of Sight:** Keine Hindernisse
5. **Höhere Position:** Berggipfel = beste Range

---

## LED Signale

**Onboard LED (GP25):**
- **ON während TX:** Sendet gerade
- **Blink bei RX:** Paket empfangen

---

## Beispiel: Complete Crisis Node

```python
# main.py - Auto-start auf Pico
from pico_sx1262_crisis_chat import CrisisChatPico
import time

# Config
USERNAME = "CrisisNode1"
NETID = 0x0034
ADDR = 0x2001
BEACON_INTERVAL = 600  # 10 Minuten

# Init
chat = CrisisChatPico(USERNAME, netid=NETID, addr=ADDR)

# Startup Message
chat.send_broadcast(f"{USERNAME} online!")

# Main Loop
msg_count = 0
while True:
    # Listen 10 Minuten
    print(f"\n[Listening for {BEACON_INTERVAL}s...]")
    chat.listen(duration=BEACON_INTERVAL)

    # Send Beacon
    msg_count += 1
    chat.send_broadcast(f"Beacon #{msg_count} - All OK")

    # Stats
    print(f"Stats: TX={chat.tx_count}, RX={chat.rx_count}")
```

---

## Weiterführende Links

**Waveshare Wiki:**
https://www.waveshare.com/wiki/Pico-LoRa-SX1262-868M

**MicroPython Docs:**
https://docs.micropython.org/en/latest/rp2/quickref.html

**SX1262 Library:**
https://github.com/ehong-tl/micropySX126X

**LoRa Calculator:**
https://www.loratools.nl/#/airtime

---

## Zusammenfassung

**Was du jetzt hast:**
- ✅ Open Source LoRa Node (kein Ebyte AT-Kommando Limit!)
- ✅ Custom Sync Word (0x11) möglich
- ✅ NetID-basiertes Routing
- ✅ WiFi + LoRa Gateway Funktion (Pico W)
- ✅ Vollständig kompatibel mit Crisis Chat System
- ✅ Interaktiver Chat Modus
- ✅ Backhaul-Filterung
- ✅ Broadcast & Unicast Support

**Nächste Schritte:**
1. Flash MicroPython auf Pico W
2. Installiere sx1262 Library
3. Kopiere pico_sx1262_crisis_chat.py
4. Konfiguriere NetID/ADDR/Username
5. Teste mit zweitem Pico oder Dragino Gateway
6. Deploy auf Berggipfel! 🏔️

Viel Erfolg! 🚀
