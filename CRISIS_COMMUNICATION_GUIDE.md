# Crisis Communication Guide
## LoRa-Based Emergency Messaging System

**Based on:** Höchst et al. (2020) - "LoRa-based Device-to-Device Smartphone Communication for Crisis Scenarios"

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Repeater Setup](#repeater-setup)
3. [Node Configuration](#node-configuration)
4. [Message Protocols](#message-protocols)
5. [Battery Management](#battery-management)
6. [Channel Plan](#channel-plan)
7. [Troubleshooting](#troubleshooting)

---

## System Overview

### Architecture

```
┌──────────────────────────────────────────────────┐
│  Berggipfel / Rooftop                            │
│  ┌────────────────────────────────────────────┐  │
│  │  Crisis Repeater Station                   │  │
│  │  • Solar Panel (50W+)                      │  │
│  │  • Battery (50Ah+)                         │  │
│  │  • 1-3 E90-DTU Modules                     │  │
│  │  • Omni-directional Antenna                │  │
│  └────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
                       │
              LoRa Broadcast (868 MHz)
                       │
        ┌──────────────┼──────────────┐
        │              │              │
  ┌─────▼────┐   ┌─────▼────┐   ┌─────▼────┐
  │  Node A  │   │  Node B  │   │  Node C  │
  │ Emergency│   │  Status  │   │  Local   │
  │  CH 23   │   │  CH 30   │   │  CH 40   │
  └──────────┘   └──────────┘   └──────────┘
```

### Design Principles (from Paper)

✅ **No prior setup required** - Users can join instantly
✅ **Public message board** - Like Twitter/CB-Funk
✅ **Channel-based topics** - Easy organization
✅ **Short messages** - Max 50 chars for efficiency
✅ **LBT enabled** - Collision avoidance
✅ **Battery-friendly** - Optional beacon mode

---

## Repeater Setup

### Hardware Requirements

| Component | Specification | Price |
|-----------|--------------|-------|
| E90-DTU Module(s) | 1-3 units (433/868/915 MHz) | €50-150 |
| Solar Panel | 50W+ | €50-100 |
| Battery | 50Ah+ (12V LiFePO4) | €100-200 |
| Antenna | Omni-directional 6-9 dBi | €20-50 |
| Enclosure | IP67 weatherproof | €30-80 |
| **Total** | | **€250-580** |

### Installation

**Location:**
- ✅ Highest point available (Berggipfel, tall building)
- ✅ 360° clear line of sight
- ✅ Away from metal objects
- ✅ Secure mounting (wind-resistant)

**Antenna:**
- Height: As high as possible (min 5m above ground)
- Type: Omni-directional (vertical polarization)
- Cable: Keep as short as possible (<5m)

### Configuration

Run the setup script:

```bash
chmod +x setup_crisis_repeater.sh
./setup_crisis_repeater.sh
```

**Choose configuration:**

| Config | Channels | Capacity | Use Case |
|--------|----------|----------|----------|
| **Single** | 1 (Emergency) | ~30 nodes | Small community |
| **Dual** | 2 (Emergency+Status) | ~60 nodes | Medium area |
| **Triple (FDM)** | 3 (Emergency+Status+Local) | ~100+ nodes | Large region |

---

## Node Configuration

### Hardware Options

**Option 1: E22 Module (Standalone)**
```
E22 LoRa Module → Raspberry Pi / Computer
Direct serial connection
```

**Option 2: E90-DTU + Smartphone (Recommended)**
```
Smartphone (iOS/Android)
    ↓ Bluetooth LE
E90-DTU Module
    ↓ LoRa (868 MHz)
Repeater
```

### Channel Selection

Choose channel based on message priority:

```bash
# Emergency (SF12 - Max Range ~3km)
./crisis_chat.py --username "Familie Müller" --channel emergency

# Status Updates (SF7 - Normal Range ~1km)
./crisis_chat.py --username "Node23" --channel status

# Local Coordination (SF7)
./crisis_chat.py --username "THW" --channel local
```

### Configuration Parameters

| Parameter | Emergency (SF12) | Status (SF7) | Local (SF7) |
|-----------|------------------|--------------|-------------|
| Channel | 23 | 30 | 40 |
| Air Baud | 300 bps | 2400 bps | 2400 bps |
| Packet Size | 50 bytes | 240 bytes | 240 bytes |
| Range (City) | ~3 km | ~1 km | ~1 km |
| Range (Rural) | ~2 km | ~1.3 km | ~1.3 km |
| LBT | ON | ON | ON |

---

## Message Protocols

### Format

Simple pipe-separated format:
```
channel|username|timestamp|message
```

**Example:**
```
emergency|Familie Müller|14:23|NOTFALL: Verletzter!
status|Schmidt|14:25|Status OK, brauche Wasser
local|THW|14:30|Treffen Marktplatz 15:00
```

### Message Types

**Emergency:**
```
NOTFALL: [Description]
Example: "NOTFALL: Verletzter Bergstr 5"
```

**Status:**
```
Status OK|Status [Bedarf]
Example: "Status OK, brauche Wasser"
```

**Information:**
```
[Short message]
Example: "Treffen Marktplatz 15:00"
```

### Message Length Limits

| Channel | Max Length | Reason |
|---------|-----------|--------|
| Emergency | **30 chars** | Fast transmission |
| Status | **50 chars** | Balance speed/content |
| Local | **100 chars** | More detailed updates |

**Important:** Keep messages SHORT!
- ✅ "NOTFALL Bergstr 5 Feuer"
- ❌ "Sehr geehrte Damen und Herren, es gibt einen Notfall..."

---

## Battery Management

### Power Consumption (from Paper)

**E90-DTU Module:**

| Mode | Power | Battery Life (20,000 mAh) |
|------|-------|---------------------------|
| Receiving (always on) | 400 mW | 6-7 days |
| Status Beacon (1×/10min) | ~10 mW avg | **40+ days** |
| Emergency Only (1× send) | 3s active | Thousands of messages |

### Recommended Node Modes

**Mode 1: Emergency Sender (Battery-Optimal)**
```bash
# Send single emergency message, then power off
./crisis_chat.py --username "Familie Müller" \
                 --channel emergency \
                 --send "NOTFALL Verletzter Bergstr 5"
```
**Battery usage:** ~3 seconds → Minimal

**Mode 2: Status Beacon (Long-Term)**
```bash
# Send status every 10 minutes
./crisis_chat.py --username "Node42" \
                 --channel status \
                 --beacon 600
```
**Battery usage:** ~10mW average → **40+ days with 20Ah powerbank**

**Mode 3: Interactive Chat (Mains-Powered)**
```bash
# Always receiving, for coordination centers
./crisis_chat.py --username "Koordination" \
                 --channel local
```
**Battery usage:** ~400mW → Requires mains power or large battery

### Battery Sizing

**Emergency Nodes (Status Beacon):**
- 20,000 mAh Powerbank = 40+ days ✅
- Typical use: 1 message per hour = months of operation

**Coordination Centers (Always On):**
- 100Ah Battery + Solar = Indefinite operation ✅
- Backup battery for night operation

---

## Channel Plan

### Frequency Plan for Crisis Communication

```
╔════════════════════════════════════════════════════════╗
║  CRISIS COMMUNICATION - FREQUENCY PLAN                ║
╠════════════════════════════════════════════════════════╣
║                                                         ║
║  📻 KANAL 23 - NOTFALL (SF12, max Reichweite)         ║
║  ├─ Reichweite: ~3km Stadt, ~2km Land                 ║
║  ├─ Priorität: HÖCHSTE                                 ║
║  ├─ Nutzer: Notfälle, Rettungsdienste                 ║
║  ├─ Sendeabstand: MINIMUM 2 Minuten                   ║
║  └─ Nachrichtenlänge: MAX 30 Zeichen                   ║
║                                                         ║
║  📻 KANAL 30 - STATUS (SF7, normale Reichweite)       ║
║  ├─ Reichweite: ~1km Stadt, ~1.3km Land               ║
║  ├─ Priorität: Normal                                  ║
║  ├─ Nutzer: Status-Updates, Allgemein                 ║
║  ├─ Sendeabstand: MINIMUM 1 Minute                    ║
║  └─ Nachrichtenlänge: MAX 50 Zeichen                   ║
║                                                         ║
║  📻 KANAL 40 - LOKAL (SF7, Koordination)              ║
║  ├─ Reichweite: ~1km Stadt, ~1.3km Land               ║
║  ├─ Priorität: Normal                                  ║
║  ├─ Nutzer: THW, Feuerwehr, Koordination              ║
║  ├─ Sendeabstand: MINIMUM 1 Minute                    ║
║  └─ Nachrichtenlänge: MAX 100 Zeichen                  ║
║                                                         ║
╚════════════════════════════════════════════════════════╝
```

### Duty Cycle Compliance (EU 868 MHz)

**Legal Limit:** 1% Duty Cycle = Max 36 seconds airtime per hour

**Practical Limits:**

| Message Length | Air-Time (SF12) | Required Pause | Max Messages/Hour |
|----------------|-----------------|----------------|-------------------|
| 30 chars | ~1.0s | 100s (1:40) | ~30 |
| 50 chars | ~1.5s | 150s (2:30) | ~20 |
| 100 chars | ~2.0s | 200s (3:20) | ~15 |

**Recommendation:** Wait **minimum 60 seconds** between messages!

---

## Usage Examples

### Scenario 1: Emergency Alert

```bash
# Family sends emergency message
./crisis_chat.py --username "Familie Müller" \
                 --channel emergency \
                 --send "NOTFALL Verletzter Bergstr 5"

# Coordination center receives and responds
# (Interactive mode - always listening)
./crisis_chat.py --username "Rettung" --channel emergency
> Empfangen von Familie Müller
> Hilfe unterwegs!
```

### Scenario 2: Status Network

```bash
# Multiple nodes send periodic status
./crisis_chat.py --username "Node1" --channel status --beacon 600 &
./crisis_chat.py --username "Node2" --channel status --beacon 600 &
./crisis_chat.py --username "Node3" --channel status --beacon 600 &

# Coordination sees all status updates
./crisis_chat.py --username "Zentrale" --channel status
```

### Scenario 3: Multi-Channel Operation

```bash
# Terminal 1: Monitor emergency
./crisis_chat.py --username "Leitstelle" --channel emergency

# Terminal 2: Monitor status
./crisis_chat.py --username "Leitstelle" --channel status

# Terminal 3: Local coordination
./crisis_chat.py --username "THW" --channel local
```

---

## Troubleshooting

### No Messages Received

**Check:**
1. ✅ Repeater powered and online?
2. ✅ Correct channel selected?
3. ✅ Within range? (Test with close distance first)
4. ✅ LBT enabled? (reduces collisions)
5. ✅ Antenna connected properly?

**Test:**
```bash
# Send test message on same channel
./crisis_chat.py --username "Test" --channel emergency --send "TEST"
```

### Messages Not Sending (Duty Cycle)

```
⏳ Duty Cycle: Wait 45s before sending
```

**Solution:** Wait! This is **legally required** in EU (868 MHz)
- After sending, wait minimum 60 seconds
- Longer messages = longer wait

### Own Messages Echoing Back (Backhaul)

This is normal with repeaters in same-network mode.

**Solution:** `crisis_chat.py` automatically filters own messages!

```python
# Automatic filter in crisis_chat.py
if line in self.sent_messages:
    continue  # Ignore own message from repeater
```

### Poor Range / Weak Signal

**Improve range:**
1. ✅ Raise antenna higher
2. ✅ Use SF12 (emergency channel)
3. ✅ Remove obstacles (line of sight!)
4. ✅ Better antenna (+3 dBi → +9 dBi)
5. ✅ Check battery level (low voltage = low power)

**Expected ranges (from Paper):**
- City, SF12: ~3 km
- Rural, SF12: ~2 km
- Forest: ~600m (blocked by trees)

### Too Many Collisions

**Symptoms:**
- Messages not getting through
- Intermittent reception

**Solutions:**
1. ✅ Ensure LBT is ON (automatic wait)
2. ✅ Enforce longer send intervals (60s minimum)
3. ✅ Use multiple channels (FDM - 3 repeaters)
4. ✅ Keep messages SHORT (<50 chars)
5. ✅ Reduce number of active nodes

**Network capacity:**
- Single channel + LBT: ~30 nodes
- Dual channel + LBT: ~60 nodes
- Triple channel + LBT: ~100+ nodes

---

## Best Practices

### For Users

✅ **Keep messages SHORT** - Every char costs airtime
✅ **Wait 60s between sends** - Duty cycle compliance
✅ **Use correct channel** - Emergency vs Status
✅ **Battery mode when possible** - Beacon instead of always-on
✅ **Test before emergency** - Know your equipment

### For Network Operators

✅ **Mount repeater HIGH** - Rooftop, tower, mountain
✅ **Solar + battery** - Survives power outages
✅ **Monitor duty cycle** - Prevent overload
✅ **Document frequencies** - Users need to know channels
✅ **Regular testing** - Monthly system checks

### For Emergency Responders

✅ **Coordinate on local channel** - Keep emergency clear
✅ **Acknowledge messages** - Let people know you received
✅ **Prioritize communications** - Emergency > Status
✅ **Have backup nodes** - Redundancy is key

---

## Reference: Paper Summary

**Höchst et al. (2020) Key Findings:**

- ✅ LoRa effective for 1-3km crisis communication
- ✅ Simple public message board works best
- ✅ LBT reduces collisions significantly
- ✅ Battery life excellent with beacon mode (40+ days)
- ✅ Smartphone + companion device = accessible to all
- ✅ No complex setup needed (instant access)

**Citation:**
> Höchst, J., Baumgärtner, L., Kuntke, F., Penning, A., Sterz, A., & Freisleben, B. (2020).
> LoRa-based Device-to-Device Smartphone Communication for Crisis Scenarios.
> Proceedings of the 17th ISCRAM Conference.

---

## Quick Start Cheat Sheet

```bash
# === REPEATER SETUP ===
./setup_crisis_repeater.sh

# === NODE USAGE ===

# Emergency (one-time send, battery optimal)
./crisis_chat.py --username "Name" --channel emergency --send "NOTFALL: Info"

# Status beacon (battery mode, sends every 10 min)
./crisis_chat.py --username "Node1" --channel status --beacon 600

# Interactive chat (mains powered)
./crisis_chat.py --username "Zentrale" --channel emergency

# === TESTING ===

# Send test message
./crisis_chat.py --username "Test" --channel status --send "TEST123"

# Monitor channel
./crisis_chat.py --username "Monitor" --channel status
```

---

**Last Updated:** 2026-01-11
**Based on:** Höchst et al. 2020 + Real-world implementation
