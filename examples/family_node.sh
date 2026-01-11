#!/bin/bash
#
# Crisis Communication - Family Node Example
# Optimized for battery life with periodic status updates
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Configuration
FAMILY_NAME="Familie Müller"
UPDATE_INTERVAL=600  # 10 minutes (battery-friendly)
CHANNEL="status"

echo "════════════════════════════════════════════════════════"
echo "  Family Emergency Node - ${FAMILY_NAME}"
echo "  Mode: Status Beacon (every 10 minutes)"
echo "  Battery: ~40 days with 20Ah powerbank"
echo "════════════════════════════════════════════════════════"
echo ""

# Check for emergency flag file
if [ -f "/tmp/emergency.flag" ]; then
    echo "🚨 EMERGENCY MODE DETECTED!"
    echo ""

    # Read emergency message
    if [ -f "/tmp/emergency_message.txt" ]; then
        EMERGENCY_MSG=$(cat /tmp/emergency_message.txt)
    else
        EMERGENCY_MSG="NOTFALL - Hilfe benötigt!"
    fi

    echo "Sending emergency message: $EMERGENCY_MSG"
    ./crisis_chat.py --username "$FAMILY_NAME" --channel emergency --send "$EMERGENCY_MSG"

    # Remove flag
    rm /tmp/emergency.flag
    rm -f /tmp/emergency_message.txt

    echo ""
    echo "✓ Emergency message sent!"
    echo "Switching to status monitoring..."
    echo ""

    sleep 5
fi

# Normal status beacon mode
echo "Starting status beacon..."
echo "Sending status every $UPDATE_INTERVAL seconds ($(($UPDATE_INTERVAL / 60)) minutes)"
echo ""
echo "To send emergency message, create flag file:"
echo "  echo 'NOTFALL Brand Bergstr 5' > /tmp/emergency_message.txt"
echo "  touch /tmp/emergency.flag"
echo ""

# Run status beacon
./crisis_chat.py \
    --username "$FAMILY_NAME" \
    --channel "$CHANNEL" \
    --beacon "$UPDATE_INTERVAL"
