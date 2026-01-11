#!/bin/bash
#
# Crisis Repeater Setup - Based on Höchst et al. 2020
# Configures E90-DTU for multi-channel crisis communication
#
# Usage: ./setup_crisis_repeater.sh
#

set -e

echo "╔════════════════════════════════════════════════════════╗"
echo "║  CRISIS REPEATER SETUP                                ║"
echo "║  Based on Höchst et al. 2020 Research                 ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Check if e90-dtu_at.py exists
if [ ! -f "./e90_dtu_at.py" ]; then
    echo "✗ Error: e90_dtu_at.py not found!"
    echo "  Make sure you're in the lora directory"
    exit 1
fi

# Configuration
read -p "Enter E90-DTU IP (default: 192.168.4.101): " DTU_IP
DTU_IP=${DTU_IP:-192.168.4.101}

echo ""
echo "Select Repeater Configuration:"
echo ""
echo "1) Single-Channel (Emergency only - SF12, max range)"
echo "2) Dual-Channel   (Emergency SF12 + Status SF7)"
echo "3) Triple-Channel (Emergency + Status + Local - FDM)"
echo ""
read -p "Choice [1-3]: " CHOICE

case $CHOICE in
    1)
        echo ""
        echo "═══ SINGLE-CHANNEL REPEATER ═══"
        echo "Channel: 23 (Emergency)"
        echo "Profile: Long Range (SF12)"
        echo "NETID: 0 ↔ 0"
        echo ""

        # Emergency Channel (SF12 - Long Range)
        python3 ./e90_dtu_at.py \
            --addr 0 \
            --netid 0 \
            --air-baud 300 \
            --pack-length 50 \
            --rssi-en RSCHON \
            --tx-pow PWMAX \
            --ch 23 \
            --rssi-data RSDATOFF \
            --tr-mod TRNOR \
            --relay RLYON \
            --lbt LBTON \
            --wor WOROFF \
            --wor-tim 2000 \
            --crypt 0

        echo "✓ Emergency channel configured on CH 23"
        ;;

    2)
        echo ""
        echo "═══ DUAL-CHANNEL REPEATER ═══"
        echo ""
        echo "⚠️  IMPORTANT: You need TWO E90-DTU modules!"
        echo ""
        echo "Module 1: CH 23 - Emergency (SF12, max range)"
        echo "Module 2: CH 30 - Status (SF7, higher capacity)"
        echo ""
        read -p "Configure Module 1 (Emergency) now? [y/N]: " CONFIRM

        if [[ $CONFIRM =~ ^[Yy]$ ]]; then
            echo ""
            echo "→ Configuring Emergency Channel (CH 23, SF12)..."

            python3 ./e90_dtu_at.py \
                --addr 0 \
                --netid 0 \
                --air-baud 300 \
                --pack-length 50 \
                --rssi-en RSCHON \
                --tx-pow PWMAX \
                --ch 23 \
                --rssi-data RSDATOFF \
                --tr-mod TRNOR \
                --relay RLYON \
                --lbt LBTON

            echo "✓ Module 1 configured"
            echo ""
            echo "Now connect Module 2 and configure Status channel:"
            echo ""
            read -p "Press Enter when ready..."

            echo ""
            echo "→ Configuring Status Channel (CH 30, SF7)..."

            python3 ./e90_dtu_at.py \
                --addr 0 \
                --netid 0 \
                --air-baud 2400 \
                --pack-length 240 \
                --rssi-en RSCHON \
                --tx-pow PWMAX \
                --ch 30 \
                --rssi-data RSDATOFF \
                --tr-mod TRNOR \
                --relay RLYON \
                --lbt LBTON

            echo "✓ Module 2 configured"
        fi
        ;;

    3)
        echo ""
        echo "═══ TRIPLE-CHANNEL REPEATER (FDM) ═══"
        echo ""
        echo "⚠️  IMPORTANT: You need THREE E90-DTU modules!"
        echo ""
        echo "Module 1: CH 23 - Emergency (SF12)"
        echo "Module 2: CH 30 - Status (SF7)"
        echo "Module 3: CH 40 - Local (SF7)"
        echo ""
        echo "This provides maximum capacity for large networks (100+ nodes)"
        echo ""
        read -p "Continue with FDM setup? [y/N]: " CONFIRM

        if [[ $CONFIRM =~ ^[Yy]$ ]]; then
            # Module 1 - Emergency
            echo ""
            echo "→ Configure Module 1 (CH 23 - Emergency)"
            read -p "Press Enter when Module 1 is connected..."

            python3 ./e90_dtu_at.py \
                --addr 0 --netid 0 --air-baud 300 --pack-length 50 \
                --rssi-en RSCHON --tx-pow PWMAX --ch 23 \
                --rssi-data RSDATOFF --tr-mod TRNOR --relay RLYON --lbt LBTON

            echo "✓ Module 1 configured (CH 23)"

            # Module 2 - Status
            echo ""
            echo "→ Configure Module 2 (CH 30 - Status)"
            read -p "Press Enter when Module 2 is connected..."

            python3 ./e90_dtu_at.py \
                --addr 0 --netid 0 --air-baud 2400 --pack-length 240 \
                --rssi-en RSCHON --tx-pow PWMAX --ch 30 \
                --rssi-data RSDATOFF --tr-mod TRNOR --relay RLYON --lbt LBTON

            echo "✓ Module 2 configured (CH 30)"

            # Module 3 - Local
            echo ""
            echo "→ Configure Module 3 (CH 40 - Local)"
            read -p "Press Enter when Module 3 is connected..."

            python3 ./e90_dtu_at.py \
                --addr 0 --netid 0 --air-baud 2400 --pack-length 240 \
                --rssi-en RSCHON --tx-pow PWMAX --ch 40 \
                --rssi-data RSDATOFF --tr-mod TRNOR --relay RLYON --lbt LBTON

            echo "✓ Module 3 configured (CH 40)"
        fi
        ;;

    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  ✓ REPEATER CONFIGURATION COMPLETE                    ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo ""
echo "1. Mount repeater at high location (Berggipfel)"
echo "2. Connect solar panel + battery"
echo "3. Configure nodes (see CRISIS_COMMUNICATION_GUIDE.md)"
echo ""
echo "Node configuration examples:"
echo ""
echo "  # Emergency channel (SF12, max range)"
echo "  ./crisis_chat.py --username \"Familie Schmidt\" --channel emergency"
echo ""
echo "  # Status channel (SF7, normal updates)"
echo "  ./crisis_chat.py --username \"Node42\" --channel status --beacon 600"
echo ""
