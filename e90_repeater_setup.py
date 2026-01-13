#!/usr/bin/python3
"""
E90-DTU (900SL30) RS485 Konfigurationsskript für Berggipfel-Repeater (1500m ü.NN)

Hardware:
- E90-DTU (900SL30) mit RS485/RS232 Schnittstelle
- USB-zu-RS485 Adapter (z.B. FTDI, CH340)
- 8-28V Stromversorgung (direkt an Solar-System)

Verwendung:
    python3 e90_repeater_setup.py --port /dev/ttyUSB0 --mode query
    python3 e90_repeater_setup.py --port /dev/ttyUSB0 --mode repeater
"""

import serial
import argparse
import time

DEFAULT_PORT = '/dev/ttyUSB0'
DEFAULT_BAUDRATE = 9600  # Standard für E90-DTU Konfiguration

def send_at_command(ser, command, wait_time=0.5, toggle_rts=False):
    """Sendet AT-Command über RS485 und gibt Antwort zurück"""
    print(f"→ Sende: {command.strip()}")
    # If using an RS485 adapter that requires driver enable, toggle RTS
    try:
        if toggle_rts:
            ser.rts = True
    except Exception:
        pass

    ser.write(command.encode())
    ser.flush()
    time.sleep(wait_time)

    response = b''
    # Read any available bytes after waiting
    while ser.in_waiting > 0:
        response += ser.read(ser.in_waiting)
        time.sleep(0.05)

    # Print both raw hex and decoded string for debugging
    if response:
        try:
            response_str = response.decode('utf-8', errors='ignore').strip()
        except Exception:
            response_str = ''
        print(f"← Empfangen (raw hex): {response.hex().upper()}")
        print(f"← Empfangen (decoded): {response_str}")
    else:
        print("← Empfangen: <no response>")

    try:
        if toggle_rts:
            ser.rts = False
    except Exception:
        pass

    return response

def configure_repeater(ser, config):
    """Konfiguriert E90-DTU als LoRa-Repeater mit RELAY-Funktion"""

    print("\n🔧 Konfiguriere E90-DTU Parameter...")
    print("-" * 60)

    # AT-Befehl für E90-DTU:
    # AT+LORA=ADDR,NETID,AIR_BAUD,PACK_LEN,RSSI_EN,TX_POW,CH,RSSI_DATA,TR_MOD,RELAY,LBT,WOR,WOR_TIM,CRYPT

    params = [
        str(config['addr']),        # Local Address (65535 = alle empfangen)
        str(config['netid']),       # Network ID
        config['air_baud'],         # Air Baud Rate
        config['pack_length'],      # Packet Length
        config['rssi_en'],          # RSSI Ambient Noise
        config['tx_pow'],           # TX Power
        str(config['channel']),     # Channel
        config['rssi_data'],        # RSSI in Data
        config['tr_mod'],           # Transfer Mode (Transparent)
        config['relay'],            # ⭐ RELAY FUNCTION
        config['lbt'],              # Listen Before Talk
        config['wor'],              # Wake on Radio
        config['wor_tim'],          # WOR Timing
        str(config['crypt'])        # Encryption Key
    ]

    command = f"AT+LORA={','.join(params)}\r\n"
    response = send_at_command(ser, command, wait_time=1.5)

    # `send_at_command` returns raw bytes. Decode safely for string checks.
    resp_str = ''
    if isinstance(response, (bytes, bytearray)):
        resp_str = response.decode('utf-8', errors='ignore')
    else:
        resp_str = str(response)

    if "OK" in resp_str or "SUCCESS" in resp_str:
        print("✅ Repeater-Konfiguration erfolgreich!")
        return True
    else:
        print("⚠️  Antwort unklar - prüfe Status manuell")
        return False

def query_status(ser):
    """Fragt aktuelle Konfiguration ab"""
    print("\n📊 E90-DTU Status:")
    print("="*60)

    # Aktuelle LoRa-Parameter abfragen
    print("\n1️⃣  LoRa Parameter:")
    send_at_command(ser, "AT+LORA\r\n", wait_time=1.0)

    # Version abfragen
    print("\n2️⃣  Firmware Version:")
    send_at_command(ser, "AT+VER\r\n", wait_time=0.5)

    # Reset-Ursache (optional, je nach Firmware)
    print("\n3️⃣  Geräte-Info:")
    send_at_command(ser, "AT+RESET\r\n", wait_time=0.5)

    print("="*60)

def main():
    parser = argparse.ArgumentParser(
        description="E90-DTU (900SL30) Berggipfel-Repeater Setup via RS485",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Status abfragen:
  %(prog)s --port /dev/ttyUSB0 --mode query

  # Als Repeater konfigurieren:
  %(prog)s --port /dev/ttyUSB0 --mode repeater

  # Mit maximaler Sendeleistung:
  %(prog)s --port /dev/ttyUSB0 --mode repeater --tx-pow PWMAX
        """
    )

    # Serielle Schnittstelle
    parser.add_argument('--port', default=DEFAULT_PORT, help='Serieller Port (z.B. /dev/ttyUSB0)')
    parser.add_argument('--baudrate', type=int, default=DEFAULT_BAUDRATE, help='Baudrate (Standard: 9600)')

    # Betriebsmodus
    parser.add_argument(
        '--mode',
        choices=['query', 'repeater', 'test'],
        default='query',
        help='Betriebsmodus'
    )

    # Repeater-Konfiguration
    parser.add_argument('--addr', type=int, default=65535, help='Local Address (65535 = Broadcast)')
    parser.add_argument('--netid', type=int, default=18, help='Network ID (18 für kompatibel mit E22)')
    parser.add_argument('--channel', type=int, default=0, help='Channel (0 = 868.1 MHz)')
    parser.add_argument('--air-baud', default='9600',
                       choices=['300', '600', '1200', '2400', '4800', '9600', '19200', '38400', '62500'],
                       help='Air Baud Rate')
    parser.add_argument('--tx-pow', default='PWMAX',
                       choices=['PWMIN', 'PWLOW', 'PWMID', 'PWMAX'],
                       help='TX Power (PWMAX empfohlen für Berg)')
    parser.add_argument('--lbt', default='LBTOFF', choices=['LBTOFF', 'LBTON'], help='Listen Before Talk (LBTOFF or LBTON)')
    parser.add_argument('--rs485', action='store_true', help='Toggle RTS around writes for RS485 transceivers')

    args = parser.parse_args()

    try:
        print("="*60)
        print("  E90-DTU (900SL30) Berggipfel-Repeater Setup")
        print("  Höhe: 1500m ü.NN | Frequenz: 868.1 MHz")
        print("="*60)
        print()

        print(f"🔌 Öffne serielle Verbindung zu {args.port} @ {args.baudrate} Baud...")

        # RS485 Verbindung öffnen
        ser = serial.Serial(
            port=args.port,
            baudrate=args.baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=2,
            write_timeout=2
        )

        time.sleep(0.5)  # Device boot time
        print("✅ Verbunden!\n")

        # Eingabe-Buffer leeren
        ser.reset_input_buffer()
        ser.reset_output_buffer()

        if args.mode == 'query':
            query_status(ser)

        elif args.mode == 'test':
            print("🧪 Test-Modus: Sende einfachen AT-Befehl...")
            send_at_command(ser, "AT\r\n")

        elif args.mode == 'repeater':
            print("🏔️  BERGGIPFEL-REPEATER KONFIGURATION")
            print("-" * 60)

            config = {
                'addr': args.addr,           # 65535 = Alle Adressen empfangen
                'netid': args.netid,         # Network ID (kompatibel mit E22)
                'air_baud': args.air_baud,   # 9600 = ~SF7 bei LoRa
                'pack_length': '240',        # Maximale Paketgröße
                'rssi_en': 'RSCHON',        # RSSI Ambient Noise: EIN
                'tx_pow': args.tx_pow,       # Maximale Sendeleistung
                'channel': args.channel,     # Kanal 0
                'rssi_data': 'RSDATON',     # RSSI in Daten: EIN
                'tr_mod': 'TRNOR',          # Transparent Mode
                'relay': 'RLYON',           # ⭐⭐⭐ RELAY AKTIVIERT ⭐⭐⭐
                'lbt': 'LBTOFF',            # LBT aus (Berg = wenig Traffic)
                    'lbt': args.lbt,            # LBT (LBTON/LBTOFF)
                'wor': 'WOROFF',            # Wake-on-Radio aus (Dauerbetrieb)
                'wor_tim': '2000',          # WOR Timing (irrelevant bei WOROFF)
                'crypt': 0                  # Keine Verschlüsselung (Repeater-Kompatibilität)
            }

            print("\n📋 Parameter:")
            for key, value in config.items():
                prefix = "⭐⭐⭐" if key == 'relay' else "   "
                print(f"{prefix} {key:15} = {value}")

            print()
            input("⚠️  Drücke ENTER zum Fortfahren (oder Strg+C zum Abbrechen)...")

            success = configure_repeater(ser, config)

            if success:
                print("\n🔍 Verifiziere Konfiguration...")
                time.sleep(1)
                query_status(ser)

                print("\n" + "="*60)
                print("✅ E90-DTU ist jetzt als REPEATER konfiguriert!")
                print("="*60)
                print("\nNächste Schritte:")
                print("1. E90-DTU auf Berg (1500m) installieren")
                print("2. 8-28V Stromversorgung anschließen (Solar)")
                print("3. Antenne montieren (+3dBi omni)")
                print("4. Reichweiten-Test mit E22 im Tal")

        ser.close()
        print("\n✅ Verbindung geschlossen")

    except serial.SerialException as e:
        print(f"\n❌ Serieller Fehler: {e}")
        print("\nPrüfe:")
        print(f"  - Ist {args.port} der richtige Port?")
        print("    (Liste mit: ls /dev/ttyUSB*)")
        print("  - Ist USB-RS485 Adapter angeschlossen?")
        print("  - Hast du die Berechtigung?")
        print("    (Führe aus: sudo usermod -a -G dialout $USER)")
    except KeyboardInterrupt:
        print("\n\n⚠️  Abgebrochen durch Benutzer")
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
