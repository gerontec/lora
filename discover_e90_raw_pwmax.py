#!/usr/bin/env python3
"""Discover vendor raw eByte sequence for setting PWMAX on E90.

Usage:
  python3 discover_e90_raw_pwmax.py --port /dev/ttyUSB0 [--rs485] [--test-send]

What it does:
  - Reads current 9-byte config via read command (C1 00 09)
  - Optionally sends AT+LORA command to set PWMAX (trigger)
  - Reads config again and compares
  - If config changed, prints candidate raw write: C0 00 09 + <9 bytes>
  - If `--test-send` is given, sends that write and re-reads to verify

This helps extract the exact vendor sequence the E90 uses to program TX power.
"""

import serial
import time
import argparse

def send_raw(ser, b):
    ser.write(b)
    ser.flush()
    time.sleep(0.2)
    return ser.read(ser.in_waiting or 256)

def read_config(ser):
    cmd = bytes([0xC1, 0x00, 0x09])
    ser.write(cmd)
    ser.flush()
    time.sleep(0.2)
    resp = ser.read(256)
    if len(resp) >= 12 and resp[0] == 0xC1:
        return resp[3:12], resp
    return None, resp

def send_at_pwmax(ser, channel, rs485=False):
    at = f"AT+LORA=65535,18,9600,240,RSCHON,PWMAX,{channel},RSDATON,TRNOR,RLYON,LBTOFF,WOROFF,2000,0\r\n"
    try:
        if rs485:
            ser.rts = True
    except Exception:
        pass
    ser.write(at.encode('utf-8'))
    ser.flush()
    time.sleep(0.6)
    resp = ser.read(ser.in_waiting or 256)
    try:
        if rs485:
            ser.rts = False
    except Exception:
        pass
    return resp

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', default='/dev/ttyUSB0')
    parser.add_argument('--baud', type=int, default=9600)
    parser.add_argument('--channel', type=int, default=17)
    parser.add_argument('--rs485', action='store_true')
    parser.add_argument('--trigger-at', action='store_true', help='Send AT+LORA PWMAX to trigger change')
    parser.add_argument('--test-send', action='store_true', help='If candidate found, send write to verify')
    args = parser.parse_args()

    ser = serial.Serial(args.port, baudrate=args.baud, timeout=1, write_timeout=1)
    time.sleep(0.2)

    before_cfg, before_raw = read_config(ser)
    print('Before raw response :', before_raw.hex().upper())
    if before_cfg is None:
        print('Failed to read config (before). Aborting.')
        ser.close()
        return
    print('Before config bytes :', before_cfg.hex().upper())

    if args.trigger_at:
        print('Sending AT+LORA PWMAX to trigger...')
        resp = send_at_pwmax(ser, args.channel, rs485=args.rs485)
        print('AT response (raw):', resp.hex().upper())

    print('Waiting 0.5s then re-reading config...')
    time.sleep(0.5)
    after_cfg, after_raw = read_config(ser)
    print('After raw response  :', after_raw.hex().upper())
    if after_cfg is None:
        print('Failed to read config (after). Aborting.')
        ser.close()
        return
    print('After config bytes  :', after_cfg.hex().upper())

    if after_cfg == before_cfg:
        print('No change detected in config bytes. The E90 did not update the 9-byte config via this trigger.')
        ser.close()
        return

    # Candidate raw write command
    write_cmd = bytes([0xC0, 0x00, 0x09]) + bytes(after_cfg)
    print('Candidate raw write:', write_cmd.hex().upper())

    if args.test_send:
        print('Sending candidate write to verify...')
        r = send_raw(ser, write_cmd)
        print('Write response raw:', r.hex().upper())
        time.sleep(0.3)
        cfg2, raw2 = read_config(ser)
        print('Verify config bytes:', cfg2.hex().upper() if cfg2 else '<none>')

    ser.close()

if __name__ == '__main__':
    main()
