#!/bin/bash
#
# Dragino - Check und Setze Custom Sync Word (z.B. 0x11)
#

DRAGINO_HOST="10.0.0.2"
TARGET_SYNC="${1:-0x11}"  # Default: 0x11

# Konvertiere zu Decimal
TARGET_DEC=$((TARGET_SYNC))

echo "╔════════════════════════════════════════════════════════╗"
echo "║  Dragino - Custom Sync Word Check & Set              ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "Target Sync Word: $TARGET_SYNC (decimal: $TARGET_DEC)"
echo ""

echo "=== 1. Prüfe global_conf.json auf lora_sync_word Parameter ==="
ssh root@${DRAGINO_HOST} "cat /etc/lora/global_conf.json 2>/dev/null | grep -i sync" || {
    echo "⚠️  global_conf.json nicht gefunden!"
    exit 1
}
echo ""

# Prüfe ob lora_sync_word Parameter existiert
if ssh root@${DRAGINO_HOST} "grep -q 'lora_sync_word' /etc/lora/global_conf.json 2>/dev/null"; then
    echo "✅ lora_sync_word Parameter gefunden!"
    echo ""

    CURRENT=$(ssh root@${DRAGINO_HOST} "grep 'lora_sync_word' /etc/lora/global_conf.json | grep -oP ':\s*\K\d+'")
    CURRENT_HEX=$(printf "0x%02X" $CURRENT)

    echo "   Aktueller Wert: $CURRENT (hex: $CURRENT_HEX)"
    echo "   Ziel-Wert:      $TARGET_DEC (hex: $TARGET_SYNC)"
    echo ""

    if [ "$CURRENT" == "$TARGET_DEC" ]; then
        echo "✅ Sync Word bereits korrekt gesetzt!"
        exit 0
    fi

    read -p "Auf $TARGET_SYNC setzen? [y/N]: " CONFIRM
    if [[ ! $CONFIRM =~ ^[Yy]$ ]]; then
        echo "Abgebrochen."
        exit 0
    fi

    echo ""
    echo "=== 2. Setze Sync Word auf $TARGET_SYNC ==="

    # Backup
    ssh root@${DRAGINO_HOST} "cp /etc/lora/global_conf.json /etc/lora/global_conf.json.backup"
    echo "   ✓ Backup erstellt: global_conf.json.backup"

    # Ändere Wert
    ssh root@${DRAGINO_HOST} "sed -i 's/\"lora_sync_word\":\s*[0-9]*/\"lora_sync_word\": $TARGET_DEC/' /etc/lora/global_conf.json"
    echo "   ✓ Sync Word auf $TARGET_DEC gesetzt"

    # Prüfe
    NEW_VAL=$(ssh root@${DRAGINO_HOST} "grep 'lora_sync_word' /etc/lora/global_conf.json | grep -oP ':\s*\K\d+'")
    echo "   ✓ Verifiziert: $NEW_VAL"
    echo ""

    echo "=== 3. Gateway Neustart ==="
    ssh root@${DRAGINO_HOST} "/etc/init.d/lora-gateway restart"
    echo "   ✓ Gateway neu gestartet"
    echo ""

    echo "Warte 5 Sekunden..."
    sleep 5

    echo ""
    echo "=== 4. Prüfe Logs ==="
    ssh root@${DRAGINO_HOST} "logread | grep -i 'sync\|lora' | tail -10"
    echo ""

    echo "════════════════════════════════════════════════════════"
    echo "✅ Sync Word erfolgreich auf $TARGET_SYNC gesetzt!"
    echo ""
    echo "Backup liegt unter: /etc/lora/global_conf.json.backup"
    echo "Zum Zurücksetzen:"
    echo "  ssh root@${DRAGINO_HOST} 'cp /etc/lora/global_conf.json.backup /etc/lora/global_conf.json'"
    echo "  ssh root@${DRAGINO_HOST} '/etc/init.d/lora-gateway restart'"
    echo "════════════════════════════════════════════════════════"

else
    echo "❌ lora_sync_word Parameter NICHT gefunden!"
    echo ""
    echo "Dein Packet Forwarder unterstützt keine custom Sync Words via JSON."
    echo ""
    echo "Verfügbare Alternativen:"
    echo ""
    echo "1. Standard Sync Words nutzen (EINFACH):"
    echo "   • 0x12 (18) - LoRaWAN Private (E22 Default)"
    echo "   • 0x34 (52) - LoRaWAN Public"
    echo "   → Setze mit: ./dragino_set_ebyte_sync.sh"
    echo ""
    echo "2. Source Code patchen (BESTE Methode):"
    echo "   → Siehe: dragino_custom_syncword_guide.md"
    echo "   • Ändere LORA_SYNCWORD_PRIVATE in sx1302_hal.c"
    echo "   • Neu kompilieren"
    echo ""
    echo "3. Binary Patching (RISKANT):"
    echo "   → Siehe: dragino_custom_syncword_guide.md"
    echo "   • Patche libloragw.so direkt"
    echo ""
    echo "════════════════════════════════════════════════════════"

    exit 1
fi
