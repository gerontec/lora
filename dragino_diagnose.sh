#!/bin/bash
#
# Dragino SX1302 - Low-Level Diagnose Script
# Findet alle Low-Level Zugriffsmöglichkeiten
#

DRAGINO_HOST="10.0.0.2"

echo "╔════════════════════════════════════════════════════════╗"
echo "║  Dragino SX1302 - Low-Level Diagnose                  ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

echo "=== 1. System Info ==="
ssh root@${DRAGINO_HOST} "uname -a && echo '' && cat /etc/openwrt_release"
echo ""

echo "=== 2. SPI Devices (Kernel Level) ==="
ssh root@${DRAGINO_HOST} "ls -la /dev/spidev* 2>/dev/null || echo 'No SPI devices found'"
echo ""

echo "=== 3. Verfügbare libloragw Tools ==="
ssh root@${DRAGINO_HOST} "ls -1 /usr/bin/test_* /usr/bin/util_* 2>/dev/null | sort"
echo ""

echo "=== 4. Chip ID auslesen (SX1302 Version) ==="
ssh root@${DRAGINO_HOST} "killall fwd 2>/dev/null; sleep 1; util_chip_id -r 1250 -k 0 2>&1 | head -20"
echo ""

echo "=== 5. GPIO Status (Reset/Enable Pins) ==="
ssh root@${DRAGINO_HOST} "cat /sys/kernel/debug/gpio 2>/dev/null | grep -A2 -B2 'lora\|reset\|sx' || echo 'GPIO debug not available (try: mount -t debugfs none /sys/kernel/debug)'"
echo ""

echo "=== 6. Packet Forwarder Config (global_conf.json) ==="
ssh root@${DRAGINO_HOST} "cat /etc/lora/global_conf.json 2>/dev/null | head -60 || echo 'Config not found'"
echo ""

echo "=== 7. UCI LoRa Settings (OpenWrt Config) ==="
ssh root@${DRAGINO_HOST} "uci show lora 2>/dev/null || echo 'UCI lora not configured'"
echo ""

echo "=== 8. Kernel Modules (SPI/LoRa) ==="
ssh root@${DRAGINO_HOST} "lsmod | grep -E 'spi|lora|sx' || echo 'No matching modules'"
echo ""

echo "=== 9. SPI Bus Info ==="
ssh root@${DRAGINO_HOST} "cat /sys/class/spi_master/spi*/device/modalias 2>/dev/null || echo 'SPI info not available'"
echo ""

echo "=== 10. Register Test (direkter Chip-Zugriff) ==="
echo "Teste Register-Zugriff..."
ssh root@${DRAGINO_HOST} "killall fwd 2>/dev/null; sleep 1; test_loragw_reg -r 1250 -k 0 2>&1 | head -30"
echo ""

echo "════════════════════════════════════════════════════════"
echo "Diagnose abgeschlossen!"
echo ""
echo "Nächste Schritte:"
echo "  1. Prüfe welche util_* Tools verfügbar sind"
echo "  2. Teste Register-Zugriff mit test_loragw_reg"
echo "  3. Siehe dragino_chip_access_guide.md für Details"
echo "════════════════════════════════════════════════════════"
