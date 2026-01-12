#!/bin/bash
#
# Dragino - Setze Sync Word auf 0x12 (Ebyte Standard)
#

DRAGINO_HOST="10.0.0.2"

echo "╔════════════════════════════════════════════════════════╗"
echo "║  Dragino - Ebyte Sync Word Konfiguration (0x12)      ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

echo "=== 1. Aktuelle Konfiguration ==="
echo -n "Aktuell: "
ssh root@${DRAGINO_HOST} "uci get lora.@lora[0].lorawan_public 2>/dev/null" && {
    CURRENT=$(ssh root@${DRAGINO_HOST} "uci get lora.@lora[0].lorawan_public")
    if [ "$CURRENT" == "1" ]; then
        echo "   → Sync Word = 0x34 (LoRaWAN Public)"
        echo "   ⚠️  NICHT kompatibel mit Ebyte E22!"
    else
        echo "   → Sync Word = 0x12 (Private Network / Ebyte)"
        echo "   ✅ Bereits kompatibel mit Ebyte E22!"
    fi
} || {
    echo "   ⚠️  UCI nicht verfügbar, prüfe global_conf.json..."
    ssh root@${DRAGINO_HOST} "cat /etc/lora/global_conf.json | grep lorawan_public"
}
echo ""

read -p "Auf Ebyte Standard (0x12) setzen? [y/N]: " CONFIRM
if [[ ! $CONFIRM =~ ^[Yy]$ ]]; then
    echo "Abgebrochen."
    exit 0
fi

echo ""
echo "=== 2. Setze Sync Word auf 0x12 ==="

# Methode 1: UCI (bevorzugt)
echo "Versuche UCI..."
ssh root@${DRAGINO_HOST} "uci set lora.@lora[0].lorawan_public=0" 2>/dev/null && {
    ssh root@${DRAGINO_HOST} "uci commit lora"
    echo "✅ UCI Konfiguration aktualisiert"
} || {
    echo "⚠️  UCI nicht verfügbar, verwende direkte global_conf.json Änderung..."
    # Methode 2: Direkte Änderung
    ssh root@${DRAGINO_HOST} "sed -i 's/\"lorawan_public\": true/\"lorawan_public\": false/' /etc/lora/global_conf.json"
    echo "✅ global_conf.json aktualisiert"
}

echo ""
echo "=== 3. Neustart Gateway ==="
ssh root@${DRAGINO_HOST} "/etc/init.d/lora-gateway restart"
echo "✅ Gateway neu gestartet"
echo ""

echo "Warte 5 Sekunden..."
sleep 5

echo ""
echo "=== 4. Verifikation ==="
ssh root@${DRAGINO_HOST} "logread | grep -i 'lorawan_public\|sync' | tail -5"
echo ""

echo "════════════════════════════════════════════════════════"
echo "✅ Sync Word auf 0x12 (Ebyte Standard) gesetzt!"
echo ""
echo "Nächste Schritte:"
echo "  1. Teste mit: ./dragino_remote_monitor.py"
echo "  2. Sende Paket von E22 Modul"
echo "  3. Dragino sollte jetzt empfangen können"
echo ""
echo "Zurück auf LoRaWAN (0x34):"
echo "  uci set lora.@lora[0].lorawan_public=1"
echo "  uci commit lora"
echo "  /etc/init.d/lora-gateway restart"
echo "════════════════════════════════════════════════════════"
