# Ebyte Firmware - Proprietary vs Open Source Alternativen

## ❌ Ebyte Firmware ist NICHT Open Source

**Was du hast:**
- E22/E90 Module mit proprietärer Ebyte Firmware
- Closed-Source Binary auf dem SX126x Chip
- AT-Kommando Interface
- Limitierte Konfiguration (Register C0-CF)

**Was du NICHT hast:**
- Quellcode der Firmware
- Möglichkeit eigene Features zu implementieren
- Direkter Zugriff auf SX126x HAL-Layer
- Flexible NetID/Addressing Protokolle

---

## ✅ Open Source Alternativen für SX126x

### 1. RadioLib (Empfohlen für Custom Protokolle)

**GitHub:** https://github.com/jgromes/RadioLib

**Features:**
- ✅ Volle SX126x Kontrolle
- ✅ Custom Sync Words
- ✅ Eigene Protokolle implementierbar
- ✅ NetID Support selbst implementierbar
- ✅ Arduino, ESP32, Raspberry Pi Support

**Beispiel:**
```cpp
#include <RadioLib.h>

// SX1262 (E22 Chip)
SX1262 radio = new Module(10, 2, 3, 9); // NSS, DIO1, RESET, BUSY

void setup() {
    // Init mit custom Sync Word
    radio.begin(867.1, 125.0, 9, 7, 0x11, 22);
    //          freq   bw    sf  cr  sync  pwr

    // Eigenes NetID Protokoll
    radio.setPacketReceivedAction(onReceive);
}

void onReceive(void) {
    uint8_t packet[256];
    int len = radio.readData(packet, 256);

    // Parse eigenes Protokoll
    uint16_t netid = (packet[0] << 8) | packet[1];
    uint16_t addr = (packet[2] << 8) | packet[3];

    // Filtere nach NetID
    if (netid != MY_NETID) return;

    // Verarbeite Daten
    processData(&packet[4], len - 4);
}

void sendWithNetID(uint16_t netid, uint16_t addr, uint8_t* data, int len) {
    uint8_t packet[256];
    packet[0] = netid >> 8;
    packet[1] = netid & 0xFF;
    packet[2] = addr >> 8;
    packet[3] = addr & 0xFF;
    memcpy(&packet[4], data, len);

    radio.transmit(packet, len + 4);
}
```

**Hardware:** Arduino/ESP32 + SX1262 Modul (z.B. E22-400M30S ohne Ebyte Firmware)

---

### 2. LoRaMac-node (LoRaWAN Stack)

**GitHub:** https://github.com/Lora-net/LoRaMac-node

**Features:**
- ✅ Offizieller Semtech LoRaWAN Stack
- ✅ Voller Source Code verfügbar
- ✅ DevAddr/NetID Support (LoRaWAN Standard)
- ✅ STM32, ESP32, nRF52 Support

**Use Case:** LoRaWAN-konformes Netzwerk mit NetID

---

### 3. sx126x-rs (Rust Driver)

**GitHub:** https://github.com/rust-iot/rust-radio-sx126x

**Features:**
- ✅ Rust Driver für SX126x
- ✅ Embedded-HAL compatible
- ✅ Eigene Protokolle implementierbar

---

### 4. PyCom/MicroPython LoRa

**GitHub:** https://github.com/micropython/micropython

**Features:**
- ✅ Python-basierte LoRa API
- ✅ ESP32 + SX126x Support
- ✅ Custom Protokolle möglich

---

## NetID Support Implementierung

### Option A: RadioLib mit Custom Protokoll

**Hardware Setup:**
- ESP32 DevKit
- E22-400M30S Modul (nackter SX1262, ohne Ebyte FW)
- 4 Kabel: NSS, MOSI, MISO, SCK (SPI)

**Firmware:**
```cpp
// NetID-basiertes Protokoll
struct LoRaPacket {
    uint16_t netid;      // Network ID
    uint16_t src_addr;   // Source Address
    uint16_t dst_addr;   // Destination Address
    uint8_t  flags;      // Control Flags
    uint8_t  payload[249]; // Max LoRa payload
};

void sendPacket(uint16_t netid, uint16_t dst, uint8_t* data, int len) {
    LoRaPacket pkt;
    pkt.netid = netid;
    pkt.src_addr = MY_ADDR;
    pkt.dst_addr = dst;
    pkt.flags = 0x00;
    memcpy(pkt.payload, data, len);

    radio.transmit((uint8_t*)&pkt, 7 + len);
}

void onReceive(void) {
    LoRaPacket pkt;
    radio.readData((uint8_t*)&pkt, sizeof(pkt));

    // Filter NetID
    if (pkt.netid != MY_NETID) return;

    // Filter Destination (Broadcast oder eigene Addr)
    if (pkt.dst_addr != MY_ADDR && pkt.dst_addr != 0xFFFF) return;

    // Process
    processPayload(pkt.payload);
}
```

---

### Option B: Ebyte Module + MCU mit Software-NetID

**Behalte Ebyte Firmware, implementiere NetID in Software:**

```python
# Python auf Raspberry Pi
import serial

MY_NETID = 0x0034
MY_ADDR = 0x1234

class EbyteWithNetID:
    def __init__(self, port):
        self.ser = serial.Serial(port, 9600)
        self.sent_messages = []

    def send(self, netid, dst_addr, data):
        # Baue Paket mit NetID Header
        packet = struct.pack('>HHH', netid, MY_ADDR, dst_addr)
        packet += data[:50]  # Max 50 Byte Payload

        self.ser.write(packet)
        self.sent_messages.append(packet)

    def receive(self):
        while self.ser.in_waiting:
            data = self.ser.read(self.ser.in_waiting)

            # Parse Paket
            if len(data) < 6:
                continue

            netid, src, dst = struct.unpack('>HHH', data[:6])
            payload = data[6:]

            # Filter NetID
            if netid != MY_NETID:
                continue

            # Filter Destination
            if dst != MY_ADDR and dst != 0xFFFF:
                continue

            # Backhaul Filter
            if data in self.sent_messages:
                continue

            return {
                'netid': netid,
                'src': src,
                'dst': dst,
                'data': payload
            }
```

**Vorteil:** Nutzt bestehende E22 Hardware ✅
**Nachteil:** NetID wird auf Software-Ebene gefiltert (nicht im Chip)

---

## Vergleich: Ebyte vs Open Source

| Feature | Ebyte FW | RadioLib | LoRaMac-node |
|---------|----------|----------|--------------|
| **Open Source** | ❌ Nein | ✅ Ja | ✅ Ja |
| **Custom Sync Word** | ⚠️ Nur 0x12/0x34 | ✅ Jeder Wert | ✅ LoRaWAN Standard |
| **NetID Support** | ⚠️ Basic Filter | ✅ Custom Protokoll | ✅ LoRaWAN DevAddr |
| **AT Commands** | ✅ Ja | ❌ Nein | ❌ Nein |
| **Easy Setup** | ✅ Sehr einfach | ⭐⭐ Mittel | ⭐⭐⭐ Komplex |
| **Flexibilität** | ⭐ Gering | ⭐⭐⭐⭐⭐ Sehr hoch | ⭐⭐⭐⭐ Hoch |
| **Hardware** | E22/E90 Module | SX126x + MCU | SX126x + MCU |

---

## Empfehlung für dein Setup

### Szenario 1: Du willst E22 Module weiter nutzen

**Lösung:** Software-NetID (Option B)
- Behalte Ebyte Firmware
- Implementiere NetID-Protokoll in Python/C auf Raspberry Pi
- E22 sendet/empfängt "roh", MCU filtert NetID

**Vorteil:** Keine Hardware-Änderung nötig ✅

---

### Szenario 2: Du willst volle Kontrolle

**Lösung:** RadioLib + ESP32 + SX1262 Modul

**Hardware:**
- ESP32 DevKit (~5€)
- E22-400M30S LoRa Modul (~8€) - **OHNE Ebyte Firmware flashen**
- Flashe eigene RadioLib-basierte Firmware

**Schritte:**
1. ESP32 + E22 Modul verkabeln (SPI)
2. RadioLib Firmware flashen
3. Eigenes NetID-Protokoll implementieren

**Vorteil:** Volle Kontrolle, custom Sync Words, optimiertes Protokoll ✅

---

### Szenario 3: LoRaWAN-kompatibel mit NetID

**Lösung:** LoRaMac-node Stack

**Use Case:** Wenn du LoRaWAN-Standard NetID/DevAddr nutzen willst
- NetID = LoRaWAN Network Identifier (7/24 bit)
- DevAddr = Device Address (25 bit)

---

## Quick Start: RadioLib NetID Demo

### Hardware:
- ESP32 DevKit
- E22-400M30S Modul

### Wiring:
```
E22 Pin    → ESP32 Pin
────────────────────────
VCC (3.3V) → 3.3V
GND        → GND
NSS        → GPIO 5
MOSI       → GPIO 23
MISO       → GPIO 19
SCK        → GPIO 18
DIO1       → GPIO 2
RESET      → GPIO 4
BUSY       → GPIO 15
```

### Code:
```cpp
#include <RadioLib.h>

SX1262 radio = new Module(5, 2, 4, 15); // NSS, DIO1, RST, BUSY

#define MY_NETID 0x0034
#define MY_ADDR  0x1234

void setup() {
    Serial.begin(115200);

    // Init mit Sync Word 0x11
    radio.begin(867.1, 125.0, 9, 7, 0x11, 22);
    radio.setPacketReceivedAction(onReceive);
    radio.startReceive();
}

void loop() {
    if (Serial.available()) {
        String msg = Serial.readStringUntil('\n');
        sendMsg(0xFFFF, msg); // Broadcast
    }
}

void sendMsg(uint16_t dst, String msg) {
    uint8_t buf[256];
    buf[0] = MY_NETID >> 8;
    buf[1] = MY_NETID & 0xFF;
    buf[2] = MY_ADDR >> 8;
    buf[3] = MY_ADDR & 0xFF;
    buf[4] = dst >> 8;
    buf[5] = dst & 0xFF;

    int len = msg.length();
    memcpy(&buf[6], msg.c_str(), len);

    radio.transmit(buf, 6 + len);
}

void onReceive(void) {
    uint8_t buf[256];
    int len = radio.readData(buf, 256);

    if (len < 6) return;

    uint16_t netid = (buf[0] << 8) | buf[1];
    uint16_t src = (buf[2] << 8) | buf[3];
    uint16_t dst = (buf[4] << 8) | buf[5];

    // NetID Filter
    if (netid != MY_NETID) return;

    // Addr Filter
    if (dst != MY_ADDR && dst != 0xFFFF) return;

    // Print
    Serial.printf("[NetID:%04X][From:%04X] ", netid, src);
    Serial.write(&buf[6], len - 6);
    Serial.println();

    radio.startReceive();
}
```

---

## Zusammenfassung

**Ebyte Firmware:**
- ❌ NICHT Open Source
- ❌ Kein flexibler NetID Support
- ❌ Limitierte Konfiguration

**Deine Optionen:**

1. **Software-NetID** auf Ebyte (einfach, begrenzt)
2. **RadioLib** auf ESP32+SX126x (beste Flexibilität)
3. **LoRaMac-node** für LoRaWAN-Standard NetID

**Empfehlung:** RadioLib für volle Kontrolle + eigenes NetID-Protokoll! 🚀
