#!/bin/bash
#
# Crisis Communication - Coordination Center
# Monitors all channels, always-on (requires mains power)
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "╔════════════════════════════════════════════════════════╗"
echo "║  CRISIS COORDINATION CENTER                           ║"
echo "║  Monitoring: Emergency + Status + Local               ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Check if tmux is available
if ! command -v tmux &> /dev/null; then
    echo "⚠️  Warning: tmux not found"
    echo "   Install with: sudo apt install tmux"
    echo ""
    echo "Running in simple mode (emergency channel only)..."
    echo ""

    ./crisis_chat.py --username "Koordination" --channel emergency
    exit 0
fi

# Create tmux session with multiple panes
SESSION="crisis_coord"

# Kill existing session if any
tmux kill-session -t $SESSION 2>/dev/null || true

# Create new session with 3 panes
tmux new-session -d -s $SESSION -n "Crisis Monitor"

# Split window into 3 panes
tmux split-window -h -t $SESSION
tmux split-window -v -t $SESSION

# Pane 0: Emergency channel (top-left)
tmux send-keys -t $SESSION:0.0 "cd $(pwd) && clear" C-m
tmux send-keys -t $SESSION:0.0 "echo '═══ EMERGENCY CHANNEL ═══'" C-m
tmux send-keys -t $SESSION:0.0 "./crisis_chat.py --username 'Zentrale' --channel emergency" C-m

# Pane 1: Status channel (top-right)
tmux send-keys -t $SESSION:0.1 "cd $(pwd) && clear" C-m
tmux send-keys -t $SESSION:0.1 "echo '═══ STATUS CHANNEL ═══'" C-m
tmux send-keys -t $SESSION:0.1 "./crisis_chat.py --username 'Zentrale' --channel status" C-m

# Pane 2: Local channel (bottom-right)
tmux send-keys -t $SESSION:0.2 "cd $(pwd) && clear" C-m
tmux send-keys -t $SESSION:0.2 "echo '═══ LOCAL CHANNEL ═══'" C-m
tmux send-keys -t $SESSION:0.2 "./crisis_chat.py --username 'Zentrale' --channel local" C-m

# Attach to session
echo "Starting multi-channel monitor..."
echo ""
echo "Channels:"
echo "  • Emergency (top-left) - Highest priority"
echo "  • Status (top-right) - Regular updates"
echo "  • Local (bottom) - Coordination"
echo ""
echo "Controls:"
echo "  • Switch panes: Ctrl+B then Arrow keys"
echo "  • Detach: Ctrl+B then D"
echo "  • Reattach: tmux attach -t $SESSION"
echo "  • Exit: Ctrl+C in each pane, then 'exit'"
echo ""
echo "Attaching to session in 3 seconds..."
sleep 3

tmux attach -t $SESSION
