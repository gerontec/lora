# Crisis Communication System

LoRa-based emergency messaging for infrastructure-less scenarios.

**Based on research:** Höchst et al. (2020) - [Paper](2020_Höchstetal_LoRaDeviceSmartphoneCommunicationCrisisScenarios.pdf)

---

## Quick Start

### 1. Setup Repeater (one-time)

```bash
./setup_crisis_repeater.sh
```

### 2. Use as Emergency Node

```bash
# Send emergency message
./crisis_chat.py --username "Your Name" --channel emergency --send "NOTFALL: Description"

# Status beacon (battery-friendly, sends every 10 min)
./crisis_chat.py --username "Your Name" --channel status --beacon 600
```

### 3. Use as Coordination Center

```bash
# Interactive chat (always listening)
./crisis_chat.py --username "Zentrale" --channel emergency
```

---

## System Components

```
crisis_chat.py                    # Main chat application
setup_crisis_repeater.sh          # Repeater configuration
test_crisis_system.sh             # System testing
CRISIS_COMMUNICATION_GUIDE.md     # Complete documentation
examples/
  ├── family_node.sh              # Battery-optimized family node
  └── coordination_center.sh      # Multi-channel monitoring
```

---

## Features

✅ **No infrastructure required** - Works when Internet/phone networks are down
✅ **Long range** - Up to 3km in cities, 2km in rural areas
✅ **Low power** - 40+ days with 20Ah battery (beacon mode)
✅ **Simple to use** - Like Twitter/CB-Funk, no complex setup
✅ **Multi-channel** - Emergency, Status, Local coordination
✅ **LBT enabled** - Automatic collision avoidance
✅ **EU legal** - Duty cycle compliant

---

## Architecture

```
    Berggipfel Repeater (Solar + Battery)
              │
    ┌─────────┼─────────┐
    │         │         │
 Emergency  Status   Local
 (SF12)     (SF7)    (SF7)
 ~3km       ~1km     ~1km
```

---

## Message Format

Simple pipe-separated protocol:
```
channel|username|time|message
```

**Example:**
```
emergency|Familie Müller|14:23|NOTFALL Verletzter Bergstr 5
status|Node42|14:25|Status OK
```

---

## Channels

| Channel | Range | Use Case | Send Interval |
|---------|-------|----------|---------------|
| **emergency** | ~3 km | 🚨 Emergencies only | Min 2 min |
| **status** | ~1 km | 📊 Status updates | Min 1 min |
| **local** | ~1 km | 🔧 Coordination | Min 1 min |

---

## Battery Life

| Mode | Power | Duration (20Ah) |
|------|-------|-----------------|
| Always-on | 400 mW | 6-7 days |
| Beacon (10min) | ~10 mW | **40+ days** ✅ |
| Emergency-only | 3s active | Thousands of msgs |

---

## Examples

### Emergency Alert
```bash
./crisis_chat.py --username "Familie Schmidt" \
                 --channel emergency \
                 --send "NOTFALL Brand Bergweg 12"
```

### Status Network
```bash
# Run on multiple nodes
./crisis_chat.py --username "Node1" --channel status --beacon 600
```

### Coordination Center
```bash
# Monitor all channels (requires tmux)
./examples/coordination_center.sh
```

---

## Testing

```bash
./test_crisis_system.sh

# Options:
# 1) Basic functionality
# 2) Range test
# 3) Battery life simulation
# 4) Multi-channel test
# 5) Stress test
```

---

## Hardware Requirements

### Repeater (Berggipfel)
- 1-3× E90-DTU modules (€50-150)
- Solar panel 50W+ (€50-100)
- Battery 50Ah+ (€100-200)
- Antenna omni 6-9dBi (€20-50)
- Weather enclosure IP67 (€30-80)

**Total: €250-580**

### Nodes (Users)
- E22/E90 LoRa module (€10-50)
- Raspberry Pi / Computer (optional)
- Powerbank 20Ah (€20-50)

**Total per node: €30-100**

---

## Documentation

📖 **[Complete Guide](CRISIS_COMMUNICATION_GUIDE.md)** - Full documentation

**Topics:**
- System overview
- Repeater installation
- Node configuration
- Message protocols
- Battery management
- Troubleshooting
- Best practices

---

## Real-World Results (from Paper)

**Range achieved:**
- City (SF12): 2.89 km
- Rural (SF12): 1.64 km
- City (SF7): 1.09 km
- Rural (SF7): 1.31 km

**Limitations:**
- Hills block signal
- Forest reduces range (~600m)
- Line-of-sight important

---

## Legal Notice

**EU 868 MHz Band:**
- ✅ Duty Cycle: 1% maximum
- ✅ 36 seconds airtime per hour
- ✅ Automatic compliance in software

**This system enforces:**
- Minimum 60s between sends
- LBT (Listen Before Talk)
- Short messages (<50 chars recommended)

---

## License

MIT License - See individual files for details

---

## Citation

Research implementation based on:

> Höchst, J., Baumgärtner, L., Kuntke, F., Penning, A., Sterz, A., & Freisleben, B. (2020).
> LoRa-based Device-to-Device Smartphone Communication for Crisis Scenarios.
> Proceedings of the 17th ISCRAM Conference – Blacksburg, VA, USA May 2020.

---

## Support

For issues or questions:
1. Check [CRISIS_COMMUNICATION_GUIDE.md](CRISIS_COMMUNICATION_GUIDE.md)
2. Run `./test_crisis_system.sh` for diagnostics
3. Review system logs

---

**Last Updated:** 2026-01-11
