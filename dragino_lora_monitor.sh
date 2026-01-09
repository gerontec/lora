#!/bin/sh
#
# LoRa Raw Packet Monitor für Dragino Gateway
# Nutzt test_loragw_hal_rx und parst die Ausgabe
#
# Installation auf Dragino:
#   scp dragino_lora_monitor.sh root@10.0.0.2:/root/
#   ssh root@10.0.0.2
#   chmod +x /root/dragino_lora_monitor.sh
#   /root/dragino_lora_monitor.sh
#

FREQ_A="867.1"
FREQ_B="868.5"
PACKET_COUNT=0

echo "=================================================="
echo "LoRa Raw Packet Monitor"
echo "=================================================="
echo "Listening on: ${FREQ_A} MHz and ${FREQ_B} MHz"
echo "Press Ctrl+C to stop"
echo ""

# Stoppe laufende Services die den LoRa-Chip blockieren
killall fwd 2>/dev/null
sleep 1

# Variablen für Packet-Parsing
FREQ=""
SIZE=""
CHAN=""
RSSI=""
SNR=""
DATA=""

# Starte test_loragw_hal_rx und parse die Ausgabe
test_loragw_hal_rx -r 1250 -a ${FREQ_A} -b ${FREQ_B} -k 0 2>&1 | while IFS= read -r line; do

    # Wenn "Waiting for packets..." erscheint
    if echo "$line" | grep -q "Waiting for packets"; then
        echo "[$(date '+%H:%M:%S')] ✓ Gateway ready - waiting for packets..."
        echo ""
    fi

    # Wenn neue Paket-Sektion beginnt
    if echo "$line" | grep -q "^----- LoRa packet -----"; then
        # Reset Variablen für neues Paket
        FREQ=""
        SIZE=""
        CHAN=""
        RSSI=""
        SNR=""
        DATA=""
    fi

    # Parse Paket-Felder
    if echo "$line" | grep -q "freq_hz"; then
        FREQ=$(echo "$line" | awk '{print $2}')
        FREQ_MHZ=$(awk "BEGIN {printf \"%.1f\", $FREQ/1000000}")
    fi

    if echo "$line" | grep -q "^  size:"; then
        SIZE=$(echo "$line" | awk '{print $2}')
    fi

    if echo "$line" | grep -q "^  chan:"; then
        CHAN=$(echo "$line" | awk '{print $2}')
    fi

    if echo "$line" | grep -q "rssi_sig"; then
        RSSI=$(echo "$line" | awk '{print $2}')
    fi

    if echo "$line" | grep -q "snr_avg"; then
        SNR=$(echo "$line" | awk '{print $2}')
    fi

    # Wenn "Received X packets" erscheint, zeige Zusammenfassung
    if echo "$line" | grep -q "Received [0-9]* packets"; then
        PACKET_COUNT=$((PACKET_COUNT + 1))

        TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

        echo "┌─ Packet #${PACKET_COUNT} ─────────────────────────────────"
        echo "│ Time:      ${TIMESTAMP}"
        echo "│ Frequency: ${FREQ_MHZ} MHz (Channel ${CHAN})"
        echo "│ Size:      ${SIZE} bytes"
        echo "│ RSSI:      ${RSSI} dBm"
        echo "│ SNR:       ${SNR} dB"

        if [ "$SIZE" -eq 0 ]; then
            echo "│ Status:    ⚠️  No payload (modulation mismatch?)"
        else
            echo "│ Status:    ✅ Payload received"
        fi

        echo "└────────────────────────────────────────────────────"
        echo ""
    fi

done

echo ""
echo "Monitor stopped. Total packets: ${PACKET_COUNT}"
