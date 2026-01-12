# Dragino - Custom Sync Word (0x11) setzen

## Problem: libloragw unterstützt NUR 0x12 und 0x34

Die `libloragw` Library (Semtech HAL) hat **hardcoded** nur zwei Sync Words:
- **0x34 (52)** - LoRaWAN Public (`lorawan_public=true`)
- **0x12 (18)** - LoRaWAN Private (`lorawan_public=false`)

**Für custom Sync Words wie 0x11 gibt es KEINE direkte API!**

---

## Lösung 1: Packet Forwarder Source Code patchen (BESTE Methode)

### Schritt 1: Sync Word in sx1302_hal.c ändern

```c
// In sx1302_hal/src/sx1302_hal.c

// Suche nach:
#define LORA_SYNCWORD_PRIVATE   0x12
#define LORA_SYNCWORD_PUBLIC    0x34

// Ändere zu:
#define LORA_SYNCWORD_PRIVATE   0x11  // Custom!
#define LORA_SYNCWORD_PUBLIC    0x34
```

### Schritt 2: Neu kompilieren

```bash
# Auf Dragino (oder Cross-Compile)
cd /path/to/sx1302_hal
make clean
make

# Installiere neue libloragw.so
cp libloragw.so /usr/lib/
```

### Schritt 3: Setze lorawan_public=false

```bash
uci set lora.@lora[0].lorawan_public=0
uci commit lora
/etc/init.d/lora-gateway restart
```

**Resultat:** Dragino nutzt jetzt 0x11 als Sync Word! ✅

---

## Lösung 2: Direkter SPI Register-Zugriff (Fortgeschritten)

```c
/*
 * dragino_custom_sync.c
 * Direkter SPI-Zugriff zum SX1250 Sync Word Register
 */

#include <stdio.h>
#include <stdint.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <linux/spi/spidev.h>

#define SPI_DEVICE      "/dev/spidev0.0"
#define SPI_SPEED       8000000  /* 8 MHz */

/* SX1302 -> SX1250 Register Access */
#define SX1302_REG_AGC_MCU_MAIL_BOX_WR_DATA  0x5600
#define SX1302_REG_AGC_MCU_MAIL_BOX_RD_DATA  0x5601
#define SX1302_REG_AGC_MCU_MAIL_BOX_CTRL     0x5602

/* SX1250 Sync Word Register (via SX1302 mailbox) */
#define SX1250_REG_LORA_SYNC_WORD_MSB        0x0740
#define SX1250_REG_LORA_SYNC_WORD_LSB        0x0741

int spi_write_read(int fd, uint8_t *tx, uint8_t *rx, int len) {
    struct spi_ioc_transfer tr = {
        .tx_buf = (unsigned long)tx,
        .rx_buf = (unsigned long)rx,
        .len = len,
        .speed_hz = SPI_SPEED,
        .bits_per_word = 8,
    };

    return ioctl(fd, SPI_IOC_MESSAGE(1), &tr);
}

int sx1302_write_register(int fd, uint16_t reg, uint8_t value) {
    uint8_t tx[4], rx[4];

    /* SX1302 SPI Write: [0x80 | MSB(addr)] [LSB(addr)] [data] */
    tx[0] = 0x80 | ((reg >> 8) & 0x7F);
    tx[1] = reg & 0xFF;
    tx[2] = value;

    return spi_write_read(fd, tx, rx, 3);
}

int sx1302_read_register(int fd, uint16_t reg, uint8_t *value) {
    uint8_t tx[4], rx[4];

    /* SX1302 SPI Read: [MSB(addr)] [LSB(addr)] [dummy] */
    tx[0] = (reg >> 8) & 0x7F;
    tx[1] = reg & 0xFF;
    tx[2] = 0x00;

    if (spi_write_read(fd, tx, rx, 3) < 0)
        return -1;

    *value = rx[2];
    return 0;
}

int set_sx1250_syncword(int fd, uint8_t sync_word) {
    printf("Setting SX1250 Sync Word to 0x%02X...\n", sync_word);

    /*
     * SX1250 Sync Word ist 16-bit (MSB + LSB)
     * LoRa Sync Word: 0x1424 → Private (0x12)
     *                 0x3444 → Public  (0x34)
     *                 0x11XX → Custom  (0x11)
     */

    uint8_t sync_msb = sync_word;
    uint8_t sync_lsb = 0x44;  /* Standard LSB */

    /* Zugriff via SX1302 AGC MCU Mailbox */
    /* Dies ist komplex - SX1302 nutzt internes Mailbox-System */

    /* Einfacherer Weg: Nutze test_loragw_reg Tool */
    printf("⚠️  Direct SPI access is complex!\n");
    printf("    Recommended: Patch sx1302_hal source code\n");

    return 0;
}

int main(int argc, char *argv[]) {
    int spi_fd;
    uint8_t sync_word;

    if (argc != 2) {
        printf("Usage: %s <sync_word_hex>\n", argv[0]);
        printf("Example: %s 0x11\n", argv[0]);
        return -1;
    }

    sync_word = (uint8_t)strtol(argv[1], NULL, 0);

    printf("Opening SPI device %s...\n", SPI_DEVICE);
    spi_fd = open(SPI_DEVICE, O_RDWR);
    if (spi_fd < 0) {
        perror("Failed to open SPI device");
        return -1;
    }

    /* Setze SPI Mode */
    uint8_t mode = SPI_MODE_0;
    ioctl(spi_fd, SPI_IOC_WR_MODE, &mode);

    /* Setze Sync Word */
    set_sx1250_syncword(spi_fd, sync_word);

    close(spi_fd);
    return 0;
}
```

**Kompilieren:**
```bash
scp dragino_custom_sync.c root@10.0.0.2:/tmp/
ssh root@10.0.0.2 "cd /tmp && gcc dragino_custom_sync.c -o custom_sync"
ssh root@10.0.0.2 "/tmp/custom_sync 0x11"
```

**Problem:** SX1302 → SX1250 Kommunikation ist komplex (Mailbox System)

---

## Lösung 3: global_conf.json mit Patch (EINFACHSTE Methode)

### Packet Forwarder mit Custom Sync Word

Einige Packet Forwarder Forks unterstützen custom Sync Word in JSON:

```json
{
  "SX130x_conf": {
    "lorawan_public": false,
    "lora_sync_word": 17     // 0x11 decimal = 17
  }
}
```

**Check ob dein Packet Forwarder das unterstützt:**

```bash
ssh root@10.0.0.2 "cat /etc/lora/global_conf.json | grep -i sync"
```

Wenn `lora_sync_word` vorhanden → **Einfach Wert ändern!**

```bash
ssh root@10.0.0.2 "sed -i 's/\"lora_sync_word\": [0-9]*/\"lora_sync_word\": 17/' /etc/lora/global_conf.json"
ssh root@10.0.0.2 "/etc/init.d/lora-gateway restart"
```

---

## Lösung 4: sx1302_hal Bibliothek mit Custom Sync Word

### Python Script zum Patchen

```python
#!/usr/bin/env python3
"""
Patch sx1302_hal library für custom Sync Word
"""

import sys

LIBLORAGW_PATH = "/usr/lib/libloragw.so"

# Suche 0x12 (Private Sync Word) im Binary
# Ersetze mit 0x11

def patch_syncword(new_sync):
    with open(LIBLORAGW_PATH, "rb") as f:
        data = bytearray(f.read())

    # Finde 0x12 Pattern (LoRa Sync Word Private)
    # Format: 0x14 0x24 (16-bit: 0x1424)
    old_pattern = bytes([0x14, 0x24])
    new_pattern = bytes([new_sync, 0x44])

    count = data.count(old_pattern)
    print(f"Found {count} occurrences of 0x{old_pattern.hex()}")

    if count == 0:
        print("No sync word pattern found!")
        return

    # Ersetze
    data = data.replace(old_pattern, new_pattern)

    # Backup
    import shutil
    shutil.copy(LIBLORAGW_PATH, LIBLORAGW_PATH + ".backup")

    # Schreibe zurück
    with open(LIBLORAGW_PATH, "wb") as f:
        f.write(data)

    print(f"✓ Patched to 0x{new_sync:02X}")
    print(f"  Backup: {LIBLORAGW_PATH}.backup")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <sync_word_hex>")
        print(f"Example: {sys.argv[0]} 0x11")
        sys.exit(1)

    sync = int(sys.argv[1], 0)
    patch_syncword(sync)
```

**Ausführung:**
```bash
scp patch_syncword.py root@10.0.0.2:/tmp/
ssh root@10.0.0.2 "python3 /tmp/patch_syncword.py 0x11"
ssh root@10.0.0.2 "/etc/init.d/lora-gateway restart"
```

**⚠️ Warnung:** Binary-Patching ist riskant!

---

## Empfehlung: Welche Methode?

| Methode | Schwierigkeit | Dauerhaft | Empfohlen |
|---------|---------------|-----------|-----------|
| **1. Source Code Patch** | ⭐⭐⭐ | ✅ Ja | ✅ BESTE |
| **2. Direct SPI** | ⭐⭐⭐⭐⭐ | ❌ Temporär | ❌ Komplex |
| **3. global_conf.json** | ⭐ | ✅ Ja | ✅ Falls unterstützt |
| **4. Binary Patch** | ⭐⭐⭐⭐ | ✅ Ja | ⚠️ Riskant |

---

## Schnellste Lösung: Prüfe global_conf.json

```bash
ssh root@10.0.0.2 "cat /etc/lora/global_conf.json"
```

**Suche nach:**
```json
"lora_sync_word": 18,    // 0x12 (decimal 18)
```

**Falls vorhanden:**
```bash
# Ändere auf 0x11 (decimal 17)
ssh root@10.0.0.2 "sed -i 's/\"lora_sync_word\": 18/\"lora_sync_word\": 17/' /etc/lora/global_conf.json"
ssh root@10.0.0.2 "/etc/init.d/lora-gateway restart"
```

**Falls NICHT vorhanden:**
→ Musst du Source Code patchen (Lösung 1)

---

## Warum 0x11?

Falls du E22 Module mit custom Sync Word hast, musst du **beide Seiten** anpassen:
- E22: Register C4 für custom Sync Word
- Dragino: Source Code oder Binary Patch

**Einfacher:** Nutze Standard 0x12 auf beiden Seiten! ✅
