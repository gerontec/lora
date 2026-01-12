# Dragino SX1302 - Low-Level Chip Zugriff

## 1. Aktueller Zugriff (dragino_remote_monitor.py)

**Methode:** libloragw HAL über `test_loragw_hal_rx`

```bash
ssh root@10.0.0.2
test_loragw_hal_rx -r 1250 -a 867.1 -b 867.3 -k 0 -m 0
```

**Library:** `/usr/lib/libloragw.so` (Semtech HAL)

---

## 2. Verfügbare libloragw Tools

Prüfe welche Tools verfügbar sind:

```bash
ssh root@10.0.0.2 "ls -la /usr/bin/test_* /usr/bin/util_*"
```

**Typische Tools:**
- `test_loragw_hal_rx` - RX Empfang (aktuell genutzt)
- `test_loragw_hal_tx` - TX Senden
- `test_loragw_reg` - Register Read/Write
- `util_spectral_scan` - Spektrum-Scan
- `util_tx_test` - TX Kontinuierlich
- `util_chip_id` - Chip-Identifikation

### Test Register-Zugriff:

```bash
ssh root@10.0.0.2 "test_loragw_reg -r 1250 -k 0"
```

Dies erlaubt direkten Register-Zugriff auf den SX1302!

---

## 3. SPI Device Zugriff (Kernel-Level)

### Finde SPI Device:

```bash
ssh root@10.0.0.2 "ls -la /dev/spidev*"
# Erwartet: /dev/spidev0.0 oder /dev/spidev1.0

ssh root@10.0.0.2 "dmesg | grep -i spi"
# Zeigt SPI Initialisierung
```

### SPI Parameter anzeigen:

```bash
ssh root@10.0.0.2 "cat /sys/class/spi_master/spi0/device/driver/module/parameters/*"
```

### Direkte SPI Kommunikation (Python):

```python
import spidev

spi = spidev.SpiDev()
spi.open(0, 0)  # /dev/spidev0.0
spi.max_speed_hz = 8000000  # 8 MHz (SX1302 default)
spi.mode = 0

# SX1302 Register lesen (Beispiel: Version Register)
# Schreibe Read-Kommando, lese Antwort
data = spi.xfer2([0x00, 0x00])  # Register 0x00
print(f"SX1302 Version: 0x{data[1]:02X}")

spi.close()
```

---

## 4. GPIO Zugriff (Reset/Enable Pins)

### Identifiziere GPIO Pins:

```bash
ssh root@10.0.0.2 "cat /sys/kernel/debug/gpio"
# Zeigt alle GPIO Zuordnungen

ssh root@10.0.0.2 "ls -la /sys/class/gpio/"
```

### SX1302 Reset Pin (typisch GPIO17 auf Dragino):

```bash
# Export GPIO
echo 17 > /sys/class/gpio/export

# Setze als Output
echo out > /sys/class/gpio/gpio17/direction

# Reset Chip (LOW → HIGH)
echo 0 > /sys/class/gpio/gpio17/value
sleep 0.1
echo 1 > /sys/class/gpio/gpio17/value

# Cleanup
echo 17 > /sys/class/gpio/unexport
```

---

## 5. Packet Forwarder Konfiguration

### Aktuelle Config lesen:

```bash
ssh root@10.0.0.2 "cat /etc/lora/global_conf.json"
```

**Wichtige Sektionen:**
- `SX130x_conf` - SX1302 Chip Konfiguration
- `radio_0`, `radio_1` - SX1250 Radio Settings
- `chan_multiSF_*` - LoRa Channel Konfiguration
- `tx_lut_*` - TX Power Lookup Table

### UCI Konfiguration (OpenWrt):

```bash
ssh root@10.0.0.2 "uci show lora"
# Zeigt alle LoRa-bezogenen UCI Settings

ssh root@10.0.0.2 "uci get lora.@lora[0].radio_type"
# Radio Type: 1250 für SX1250
```

---

## 6. Kernel Module und Device Tree

### Geladene Kernel Module:

```bash
ssh root@10.0.0.2 "lsmod | grep -E 'spi|lora|sx'"
```

### Device Tree Informationen:

```bash
ssh root@10.0.0.2 "cat /proc/device-tree/soc/spi@*/status"
ssh root@10.0.0.2 "find /proc/device-tree -name '*spi*' -o -name '*lora*'"
```

---

## 7. Register-Level Zugriff (C/C++ Code)

### Direkt mit libloragw:

```c
#include "loragw_hal.h"
#include "loragw_reg.h"

// Öffne Gateway
struct lgw_conf_board_s boardconf;
memset(&boardconf, 0, sizeof boardconf);
boardconf.lorawan_public = true;
boardconf.clksrc = 0;  // Radio A als Clock Source

lgw_board_setconf(&boardconf);
lgw_start();

// Lese SX1302 Version Register
uint8_t version;
lgw_reg_r(0x00, &version);
printf("SX1302 Version: 0x%02X\n", version);

// Schreibe Register (Beispiel)
lgw_reg_w(0x10, 0x42);  // Register 0x10 = 0x42

// Cleanup
lgw_stop();
```

### Kompilieren auf Dragino:

```bash
scp my_test.c root@10.0.0.2:/tmp/
ssh root@10.0.0.2 "cd /tmp && gcc my_test.c -o my_test -lloragw -L/usr/lib -I/usr/include/lora"
ssh root@10.0.0.2 "/tmp/my_test"
```

---

## 8. Diagnose-Kommandos (Start hier!)

### Kopiere diese Kommandos und führe sie aus:

```bash
# === System Info ===
ssh root@10.0.0.2 "uname -a; cat /etc/openwrt_release"

# === SPI Devices ===
ssh root@10.0.0.2 "ls -la /dev/spidev*"

# === Verfügbare libloragw Tools ===
ssh root@10.0.0.2 "ls -la /usr/bin/test_* /usr/bin/util_*"

# === Chip ID auslesen ===
ssh root@10.0.0.2 "killall fwd 2>/dev/null; util_chip_id -r 1250 -k 0"

# === GPIO Status ===
ssh root@10.0.0.2 "cat /sys/kernel/debug/gpio 2>/dev/null || echo 'GPIO debug not available'"

# === Packet Forwarder Config ===
ssh root@10.0.0.2 "cat /etc/lora/global_conf.json | head -50"

# === UCI LoRa Settings ===
ssh root@10.0.0.2 "uci show lora 2>/dev/null || echo 'UCI lora not configured'"

# === Register Test (direkt) ===
ssh root@10.0.0.2 "killall fwd 2>/dev/null; test_loragw_reg -r 1250 -k 0"
```

---

## 9. Zugriffs-Ebenen Zusammenfassung

| Ebene | Tool/Methode | Komplexität | Use Case |
|-------|--------------|-------------|----------|
| **Highest (Einfach)** | packet_forwarder | ⭐ | LoRaWAN Gateway Betrieb |
| **HAL Tools** | test_loragw_hal_rx/tx | ⭐⭐ | Schnelles Testen, Monitoring |
| **Register Access** | test_loragw_reg | ⭐⭐⭐ | Chip-spezifische Config |
| **libloragw C API** | loragw_hal.h | ⭐⭐⭐⭐ | Custom Anwendungen |
| **SPI Direct** | /dev/spidev + spidev lib | ⭐⭐⭐⭐⭐ | Kernel-nahe Entwicklung |
| **Lowest (Schwierig)** | GPIO + Bit-Banging | ⭐⭐⭐⭐⭐⭐ | Hardware-Debug |

---

## 10. Häufige Low-Level Tasks

### Reset SX1302 Chip:

```bash
ssh root@10.0.0.2 "killall fwd; util_chip_id -r 1250 -k 0"
# util_chip_id macht automatisch Reset + Chip ID auslesen
```

### Spektrum-Scan (Frequenz-Analyse):

```bash
ssh root@10.0.0.2 "killall fwd; util_spectral_scan -r 1250 -f 867.1"
```

### Kontinuierliches Senden (TX Test):

```bash
ssh root@10.0.0.2 "killall fwd; util_tx_test -r 1250 -f 867.1 -m LORA -b 125 -s 9 -p 14"
# -b 125 = Bandwidth 125kHz
# -s 9 = SF9
# -p 14 = Power 14dBm
```

### Register Dump (alle Register auslesen):

```bash
ssh root@10.0.0.2 "killall fwd; test_loragw_reg -r 1250 -k 0 -d"
```

---

## Nächste Schritte

1. **Führe Diagnose-Kommandos aus** (Sektion 8)
2. **Identifiziere verfügbare Tools** auf deinem Dragino
3. **Teste Register-Zugriff** mit test_loragw_reg
4. **Experimentiere mit util_* Tools** für spezifische Tasks

Welche Zugriffs-Ebene brauchst du? Was ist dein Ziel?
