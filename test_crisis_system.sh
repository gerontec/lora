#!/bin/bash
#
# Crisis Communication System - Test Script
# Tests basic functionality before deployment
#

set -e

echo "╔════════════════════════════════════════════════════════╗"
echo "║  CRISIS COMMUNICATION SYSTEM - TEST                   ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Check if crisis_chat.py exists
if [ ! -f "./crisis_chat.py" ]; then
    echo "✗ Error: crisis_chat.py not found!"
    exit 1
fi

# Make executable
chmod +x crisis_chat.py

echo "Tests:"
echo ""
echo "1) Basic Functionality Test"
echo "2) Range Test (requires 2 nodes)"
echo "3) Battery Life Simulation"
echo "4) Multi-Channel Test"
echo "5) Stress Test (collision testing)"
echo ""
read -p "Select test [1-5]: " TEST_CHOICE

case $TEST_CHOICE in
    1)
        echo ""
        echo "═══ BASIC FUNCTIONALITY TEST ═══"
        echo ""
        echo "This test sends a single message and listens for 30 seconds"
        echo ""
        read -p "Enter your username: " USERNAME
        read -p "Enter test message: " MESSAGE

        echo ""
        echo "Sending message..."
        ./crisis_chat.py --username "$USERNAME" --channel test --send "$MESSAGE"

        echo ""
        echo "Listening for 30 seconds (press Ctrl+C to stop)..."
        timeout 30 ./crisis_chat.py --username "Monitor" --channel test || true

        echo ""
        echo "✓ Basic test complete"
        ;;

    2)
        echo ""
        echo "═══ RANGE TEST ═══"
        echo ""
        echo "Instructions:"
        echo "1. Start this on Node 1 (stationary)"
        echo "2. On Node 2, move away while sending messages"
        echo "3. Note maximum distance where messages still arrive"
        echo ""
        read -p "Press Enter to start monitoring..."

        echo ""
        echo "Monitoring for range test messages..."
        echo "Node 2 should send: ./crisis_chat.py --username Node2 --channel test --send \"Range test XXXm\""
        echo ""

        ./crisis_chat.py --username "RangeTest" --channel test
        ;;

    3)
        echo ""
        echo "═══ BATTERY LIFE SIMULATION ═══"
        echo ""
        echo "Simulating status beacon mode (1 message every 60 seconds)"
        echo "Running for 5 minutes to estimate battery life..."
        echo ""

        read -p "Start simulation? [y/N]: " CONFIRM
        if [[ ! $CONFIRM =~ ^[Yy]$ ]]; then
            exit 0
        fi

        echo ""
        echo "Starting 5-minute simulation..."
        echo "Expected: ~5 messages sent"
        echo ""

        # Run for 5 minutes
        timeout 300 ./crisis_chat.py --username "BatteryTest" --channel test --beacon 60 || true

        echo ""
        echo "Simulation complete!"
        echo ""
        echo "Battery life estimation:"
        echo "- Messages sent: ~5"
        echo "- With 20,000 mAh powerbank:"
        echo "  → 1 msg/min = ~40 days"
        echo "  → 1 msg/10min = ~400 days!"
        ;;

    4)
        echo ""
        echo "═══ MULTI-CHANNEL TEST ═══"
        echo ""
        echo "Testing communication on multiple channels"
        echo "This requires multiple terminals or nodes"
        echo ""
        echo "Instructions:"
        echo ""
        echo "Terminal 1 (Emergency):"
        echo "  ./crisis_chat.py --username User1 --channel emergency"
        echo ""
        echo "Terminal 2 (Status):"
        echo "  ./crisis_chat.py --username User2 --channel status"
        echo ""
        echo "Terminal 3 (Local):"
        echo "  ./crisis_chat.py --username User3 --channel local"
        echo ""
        echo "Send messages on each channel and verify isolation"
        echo ""
        read -p "Which channel to monitor? [emergency/status/local]: " CHANNEL

        ./crisis_chat.py --username "Monitor" --channel "$CHANNEL"
        ;;

    5)
        echo ""
        echo "═══ STRESS TEST (Collision Testing) ═══"
        echo ""
        echo "⚠️  WARNING: This test violates duty cycle limits!"
        echo "    Use only for testing, not in production!"
        echo ""
        read -p "Continue? [y/N]: " CONFIRM
        if [[ ! $CONFIRM =~ ^[Yy]$ ]]; then
            exit 0
        fi

        echo ""
        echo "Sending rapid messages to test collision handling..."
        echo ""

        for i in {1..10}; do
            ./crisis_chat.py --username "StressTest" --channel test --send "Message $i" &
            sleep 0.5
        done

        wait

        echo ""
        echo "✓ Stress test complete"
        echo "Check logs for collisions and retransmissions"
        ;;

    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "═══════════════════════════════════════════════════════"
echo "Test complete!"
echo ""
echo "Next steps:"
echo "1. Review CRISIS_COMMUNICATION_GUIDE.md for deployment"
echo "2. Configure repeater with setup_crisis_repeater.sh"
echo "3. Train users on basic operations"
echo ""
