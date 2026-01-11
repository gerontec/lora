# E22 Module Addressing and Status Guide

This document provides detailed information about addressing modes, module status indicators, and operational details for E22-series LoRa modules.

**Source:** E22-T Series Module User Manual (Copyright ©2012–2024, Chengdu Ebyte Electronic Technology Co., Ltd.)

---

## Table of Contents
- [Broadcast Address](#broadcast-address)
- [Listening Address](#listening-address)
- [Module Reset](#module-reset)
- [Module Status Detail](#module-status-detail)

---

## Broadcast Address

**Example:** Set the address of module A to `0xFFFF` and the channel to `0x04`.

When module A is transmitting (same mode, transparent transmission mode), all receiving modules under `0x04` channel can receive data for broadcasting purpose.

### Use Case
- **Module A Configuration:**
  - Address: `0xFFFF` (broadcast address)
  - Channel: `0x04`
  - Mode: Transparent transmission

- **Result:** All modules listening on channel `0x04` will receive the transmitted data, regardless of their individual addresses.

---

## Listening Address

**Example:** Set the address of module A to `0xFFFF` and the channel to `0x04`.

When module A acts as a receiver, it can receive all the data under `0x04` channel to achieve the purpose of listening.

### Use Case
- **Module A Configuration:**
  - Address: `0xFFFF` (promiscuous/listening mode)
  - Channel: `0x04`
  - Mode: Receiver

- **Result:** Module A will receive all transmissions on channel `0x04`, regardless of the destination address in the packets.

---

## Module Reset

After the module is powered on, the indicator light behaves in red and carries out a hardware self-test, as well as setting the working mode according to the user parameters.

During this process, the red indicator is always on, and when it is finished, the green indicator is always on and it enters the transmission mode to start normal operation.

**Important:** Users need to wait for the green indicator to be always on as the starting point for the module to work normally.

### Reset Sequence
1. **Power On** → Red LED turns on
2. **Hardware Self-Test** → Red LED remains on
3. **Configuration Loading** → Red LED remains on
4. **Ready State** → Green LED turns on (module ready for operation)

---

## Module Status Detail

The two-color LED is used to indicate the module's operating mode and operating status.

It indicates if the module is transmitting data, or responding to a received command, or if the module is in the process of initializing a self-test.

### Module Power-up Initialization Process

- **Red Indicator:** The module power-on indicator behaves red, indicating that the mode is in the power-on initialization self-test process.

- **Green Indicator:** After the module initialization self-test is completed, the indicator switches from red to green, indicating that the self-test is completed and the mode enters transmission mode (after the module is powered on and reset, it enters transmission mode).

### Wireless Transmit Indication

#### Buffer Empty (Green LED Always On)
The data in the internal 1000-byte buffer are written to the wireless chip (automatic packetization).

When the green indicator is **always on**, the user can initiate data less than 1000 bytes, which will not overflow.

#### Buffer Not Empty (Green LED Blinking)
The data in the internal 1000-byte buffer are not all written to the wireless chip and ready to transmit. At this time the module may be waiting for the end of the user data timeout, or is in the process of wireless sub-packet launch.

**Note:** When the green light is on, it does not mean that all the serial data of the module has been emitted through wireless, or the last packet of data is being emitted.

### LED Status Summary

| LED Color | LED State | Module Status |
|-----------|-----------|---------------|
| Red | Always On | Power-on initialization / Self-test in progress |
| Green | Always On | Ready / Buffer empty / Can accept new data |
| Green | Blinking | Transmitting / Buffer not empty / Processing data |

---

## Important Notes

1. **Broadcast Address:** `0xFFFF` serves dual purpose - both for broadcasting to all receivers and for listening to all transmitters on a channel.

2. **Buffer Management:** The module has a 1000-byte internal buffer. Monitor the LED status to ensure data is not sent when the buffer is full.

3. **Startup Delay:** Always wait for the green LED to be on before sending data after power-up or reset.

4. **Transmission Confirmation:** A solid green LED does not guarantee that all data has been wirelessly transmitted - it only indicates the buffer status.

---

## Related Documentation

- [E90 DTU Guide](E90_DTU_GUIDE.md)
- [Repeater Deployment](REPEATER_DEPLOYMENT.md)
- [E90 Lockout Prevention](E90_LOCKOUT_PREVENTION.md)

---

*Last Updated: 2026-01-11*
