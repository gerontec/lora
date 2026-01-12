# Raspberry Pi Pico W + LoRa HAT - Open Source Guide

## Wichtig: LoRa HATs haben KEINE Firmware!

**Unterschied zu Ebyte Modulen:**
- **Ebyte E22/E90:** SX126x Chip + proprietäre Firmware → AT-Kommandos
- **LoRa HAT:** Nackter SX126x/SX127x Chip → **DU schreibst den Code!** ✅

**Das bedeutet:**
- ✅ Volle Kontrolle über alles (Sync Word, NetID, Protokoll)
- ✅ Open Source Libraries verfügbar
- ✅ Perfekt für custom Crisis-Chat mit NetID!

---

## Häufige LoRa HATs für Pico

### 1. Waveshare Pico-LoRa-SX1262-868M HAT
**Chip:** Semtech SX1262
**Frequenz:** 868 MHz (EU)
**Interface:** SPI
**Open Source:** ✅ Beispielcode verfügbar

**Specs:**
- Spreading Factor: SF5-SF12
- Bandwidth: 125/250/500 kHz
- TX Power: bis 22 dBm
- Pins: NSS, MOSI, MISO, SCK, RESET, BUSY, DIO1

---

### 2. SB Components Pico LoRa Expansion
**Chip:** SX1276 oder SX1262
**Frequenz:** 433/868/915 MHz
**Interface:** SPI

---

### 3. Adafruit RFM95W LoRa Radio (SX1276)
**Chip:** Hope RFM95W (basierend auf SX1276)
**Frequenz:** 868/915 MHz
**Interface:** SPI

---

## Welches HAT hast du?

Prüfe:
```bash
# Wenn du SSH Zugriff zum Pico hast
# Oder prüfe die Aufschrift auf dem HAT

# Typische Beschriftung:
# "Waveshare Pico-LoRa-SX1262"
# "SX1262 868M"
# "RFM95W"
```

---

## Open Source Software Stack für Pico + LoRa

### Option 1: MicroPython mit LoRa Library (EINFACHSTE)

**Library:** https://github.com/ehong-tl/micropySX126X

**Installation:**
```python
# Auf Pico W (via Thonny oder rshell)
import mip
mip.install('github:ehong-tl/micropySX126X')
```

**Beispiel Code:**
```python
from sx1262 import SX1262
import time

# Pin-Konfiguration für Waveshare HAT
sx = SX1262(spi_bus=1, clk=10, mosi=11, miso=12, cs=3, irq=20, rst=15, gpio=2)

# Konfiguration
sx.begin(freq=868.1,         # 868.1 MHz (E22 Ch17)
         bw=125.0,           # 125 kHz
         sf=9,               # SF9 (2.4k air rate)
         cr=7,               # 4/7 coding rate
         syncWord=0x11,      # Custom Sync Word! ✅
         power=22,           # 22 dBm
         currentLimit=140,
         preambleLength=8,
         implicit=False,
         implicitLen=0xFF,
         crcOn=True,
         txIq=False,
         rxIq=False,
         tcxoVoltage=1.7,
         useRegulatorLDO=False,
         blocking=True)

print("LoRa initialized with Sync Word 0x11")

# Empfangen
def on_receive(data):
    msg = bytes(data).decode()
    print(f"Received: {msg}")

sx.setBlockingCallback(False, on_receive)

# Senden
sx.send("Hello from Pico!")

while True:
    time.sleep(1)
```

**Vorteile:**
- ✅ Python (einfach!)
- ✅ Custom Sync Word support
- ✅ Volle Kontrolle

---

### Option 2: CircuitPython mit RFM9x Library

**Library:** https://github.com/adafruit/Adafruit_CircuitPython_RFM9x

```python
import board
import busio
import digitalio
from adafruit_rfm9x import RFM9x

# SPI Setup
spi = busio.SPI(board.GP10, MOSI=board.GP11, MISO=board.GP12)
cs = digitalio.DigitalInOut(board.GP3)
reset = digitalio.DigitalInOut(board.GP15)

# RFM95W (SX1276)
rfm9x = RFM9x(spi, cs, reset, 868.1)
rfm9x.tx_power = 22
rfm9x.spreading_factor = 9
rfm9x.signal_bandwidth = 125000

# Senden
rfm9x.send("Hello from Pico!")

# Empfangen
packet = rfm9x.receive()
if packet:
    print(f"Received: {packet.decode()}")
```

---

### Option 3: C/C++ mit RadioLib (MAXIMALE Performance)

**Library:** https://github.com/jgromes/RadioLib

**Pico SDK Setup erforderlich**, aber beste Performance!

---

## NetID-Protokoll auf Pico implementieren

### MicroPython Beispiel mit NetID:

```python
from sx1262 import SX1262
import struct
import time

# === Konfiguration ===
MY_NETID = 0x0034
MY_ADDR = 0x1234

# === LoRa Init ===
sx = SX1262(spi_bus=1, clk=10, mosi=11, miso=12, cs=3, irq=20, rst=15, gpio=2)
sx.begin(freq=868.1, bw=125.0, sf=9, cr=7, syncWord=0x11, power=22)

# === Message History (Backhaul Filter) ===
sent_messages = []
MAX_HISTORY = 50

# === NetID Protokoll ===
def send_message(netid, dst_addr, payload):
    """
    Paket-Format:
    [NetID:2][SrcAddr:2][DstAddr:2][Payload:max 249]
    """
    # Build packet
    packet = struct.pack('>HHH', netid, MY_ADDR, dst_addr)
    packet += payload.encode() if isinstance(payload, str) else payload

    # Send
    sx.send(list(packet))

    # Remember (backhaul filter)
    sent_messages.append(packet)
    if len(sent_messages) > MAX_HISTORY:
        sent_messages.pop(0)

    print(f"[TX] NetID:{netid:04X} To:{dst_addr:04X} Len:{len(payload)}")

def on_receive(data):
    """Empfange und filtere nach NetID"""
    packet = bytes(data)

    # Check minimum size
    if len(packet) < 6:
        print("[RX] Packet too short")
        return

    # Parse header
    netid, src_addr, dst_addr = struct.unpack('>HHH', packet[:6])
    payload = packet[6:]

    # Backhaul filter (eigene Pakete ignorieren)
    if packet in sent_messages:
        print("[RX] Backhaul detected, ignoring")
        return

    # NetID filter
    if netid != MY_NETID:
        print(f"[RX] Wrong NetID: {netid:04X} (expected {MY_NETID:04X})")
        return

    # Address filter
    if dst_addr != MY_ADDR and dst_addr != 0xFFFF:
        print(f"[RX] Not for me: {dst_addr:04X} (I am {MY_ADDR:04X})")
        return

    # Valid packet!
    print(f"[RX] NetID:{netid:04X} From:{src_addr:04X} Len:{len(payload)}")
    try:
        print(f"     Data: {payload.decode()}")
    except:
        print(f"     Data: {payload.hex()}")

# Set callback
sx.setBlockingCallback(False, on_receive)

# === Main Loop ===
print("="*50)
print(f"Pico LoRa Chat - NetID:{MY_NETID:04X} Addr:{MY_ADDR:04X}")
print("="*50)

# Test: Send broadcast
send_message(MY_NETID, 0xFFFF, "Hello from Pico!")

# Listen
while True:
    time.sleep(1)
```

---

## Pin-Konfiguration für verschiedene HATs

### Waveshare Pico-LoRa-SX1262-868M:
```python
SPI1:
  SCK  = GP10
  MOSI = GP11
  MISO = GP12
  CS   = GP3

LoRa Control:
  RESET = GP15
  BUSY  = GP2
  DIO1  = GP20
```

### Generic SX1276/RFM95W HAT:
```python
SPI:
  SCK  = GP10 (oder GP18)
  MOSI = GP11 (oder GP19)
  MISO = GP12 (oder GP16)
  CS   = GP3

LoRa Control:
  RESET = GP15
  DIO0  = GP20  # Für SX1276
```

**Prüfe dein HAT Schematic für genaue Pins!**

---

## Vorteil: Pico W + LoRa HAT vs Ebyte

| Feature | Ebyte E22 | Pico + LoRa HAT |
|---------|-----------|-----------------|
| **Firmware** | Proprietär | ✅ DEIN Code! |
| **Sync Word** | Nur 0x12/0x34 | ✅ Beliebig (0x00-0xFF) |
| **NetID** | Basic Filter | ✅ Eigenes Protokoll |
| **Libraries** | AT Commands | ✅ MicroPython, C++ |
| **WiFi** | ❌ Nein | ✅ Pico W hat WiFi! |
| **Debugging** | Schwierig | ✅ REPL, USB Serial |
| **Preis** | ~8€ | ~8€ (Pico) + ~12€ (HAT) |

---

## Integration mit Dragino Gateway

### Pico als Crisis Chat Node:

**Setup:**
1. Pico W sendet mit Sync Word 0x11
2. Dragino Gateway empfängt (mit custom Sync Word, siehe dragino_custom_syncword_guide.md)
3. Python Script auf Server (heissa.de) parsed NetID-Pakete

**Workflow:**
```
Pico 1 (NetID:0x34, Addr:0x1001)
   ↓ LoRa (Sync:0x11, SF9, 868.1MHz)
   ↓
Dragino Gateway (10.0.0.2)
   ↓ SSH
   ↓
heissa.de Server
   ↓ Parse NetID Protokoll
   ↓
Crisis Chat Database
```

---

## Quick Start: Pico LoRa NetID Demo

### 1. Flash MicroPython auf Pico W:
```bash
# Download: https://micropython.org/download/rp2-pico-w/
# Halte BOOTSEL beim Einstecken
# Kopiere .uf2 file auf RPI-RP2 Drive
```

### 2. Installiere LoRa Library:
```python
# Via Thonny IDE
import mip
mip.install('github:ehong-tl/micropySX126X')
```

### 3. Kopiere NetID Code (siehe oben)

### 4. Test:
```python
# Terminal 1: Pico 1 (Addr 0x1001)
send_message(0x0034, 0xFFFF, "Test from Node 1")

# Terminal 2: Pico 2 (Addr 0x1002)
# Empfängt automatisch via Callback
# [RX] NetID:0034 From:1001 Len:16
#      Data: Test from Node 1
```

---

## Nächste Schritte

1. **Identifiziere dein LoRa HAT Modell** (Aufschrift prüfen)
2. **Flash MicroPython** auf Pico W
3. **Teste LoRa Kommunikation** mit Beispielcode
4. **Implementiere NetID-Protokoll**
5. **Integriere mit Dragino Gateway**

---

## Wo finde ich mehr Info?

**MicroPython LoRa Libraries:**
- https://github.com/ehong-tl/micropySX126X (SX1262)
- https://github.com/Wei1234c/SX127x_driver_for_MicroPython_on_ESP8266 (SX1276)

**Waveshare Docs:**
- https://www.waveshare.com/wiki/Pico-LoRa-SX1262-868M

**Pico W:**
- https://www.raspberrypi.com/documentation/microcontrollers/raspberry-pi-pico.html

---

## Fazit

**Dein Pico W + LoRa HAT ist PERFEKT für:**
- ✅ Open Source NetID-Protokoll
- ✅ Custom Sync Words (0x11)
- ✅ Integration mit Dragino Gateway
- ✅ WiFi + LoRa Gateway Node (Pico W hat WiFi!)
- ✅ Crisis Communication System

**Viel besser als Ebyte für custom Protokolle!** 🚀
