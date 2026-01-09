#!/usr/bin/python3
"""
E22 USB Konfiguration für LoRa Repeater Test
Konfiguriert E22 auf exakt die gleichen Parameter wie lorarep.py

Parameter:
- Frequenz: 868.1 MHz
- Spreading Factor: SF7
- Bandwidth: 125 kHz
- Code Rate: 4/5
- Power: 14 dBm (max für EU868)
"""

import serial
import time
import sys

# Serieller Port (anpassen falls nötig)
SERIAL_PORT = "/dev/ttyUSB0"  # Ändern zu deinem Port
BAUD_RATE = 9600

# LoRa Parameter (passend zu lorarep.py)
FREQ_MHZ = 868.1          # 868.1 MHz
SPREADING_FACTOR = 7      # SF7
BANDWIDTH = 125           # 125 kHz
POWER_DBM = 14           # 14 dBm (EU868 max)
ADDRESS = 0              # Broadcast
NETWORK_ID = 0           # Standard

def send_at_command(ser, command, wait_time=1):
    """Sendet AT-Befehl und liest Antwort"""
    print(f"Sende: {command}")
    ser.write((command + "\r\n").encode())
    time.sleep(wait_time)

    response = ""
    while ser.in_waiting:
        response += ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
        time.sleep(0.1)

    print(f"Antwort: {response.strip()}")
    return response

def configure_e22():
    """Konfiguriert E22 für Repeater-Test"""
    try:
        print(f"Öffne {SERIAL_PORT} mit {BAUD_RATE} baud...")
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)  # Warten bis Port bereit

        print("\n" + "="*60)
        print("E22 Konfiguration für LoRa Repeater Test")
        print("="*60)

        # 1. AT-Modus testen
        print("\n1. Teste AT-Kommunikation...")
        response = send_at_command(ser, "AT")
        if "OK" not in response:
            print("⚠️  Warnung: Keine AT-Antwort. Ist der E22 im AT-Modus? (M0=1, M1=1)")

        # 2. Aktuelle Konfiguration auslesen
        print("\n2. Lese aktuelle Konfiguration...")
        send_at_command(ser, "AT+CFG?")

        # 3. Frequenz setzen (868.1 MHz)
        print(f"\n3. Setze Frequenz auf {FREQ_MHZ} MHz...")
        # E22 Frequenz als Integer in MHz * 10 (868.1 = 8681)
        freq_param = int(FREQ_MHZ * 10)
        send_at_command(ser, f"AT+BAND={freq_param}")

        # 4. Spreading Factor setzen
        print(f"\n4. Setze Spreading Factor: SF{SPREADING_FACTOR}...")
        # E22: SF5=0, SF6=1, SF7=2, SF8=3, SF9=4, SF10=5, SF11=6, SF12=7
        sf_map = {5: 0, 6: 1, 7: 2, 8: 3, 9: 4, 10: 5, 11: 6, 12: 7}
        sf_param = sf_map.get(SPREADING_FACTOR, 2)
        send_at_command(ser, f"AT+PARAMETER={sf_param},7,1,7")  # SF, BW, CR, Preamble
        # Parameter: SF, BW(125kHz=7), CR(4/5=1), Preamble(7)

        # 5. TX Power setzen
        print(f"\n5. Setze TX Power: {POWER_DBM} dBm...")
        send_at_command(ser, f"AT+POWER={POWER_DBM}")

        # 6. Adresse und Network ID
        print(f"\n6. Setze Address={ADDRESS}, Network ID={NETWORK_ID}...")
        send_at_command(ser, f"AT+ADDRESS={ADDRESS}")
        send_at_command(ser, f"AT+NETWORKID={NETWORK_ID}")

        # 7. Modus: Transparent
        print("\n7. Setze Modus: Transparent...")
        send_at_command(ser, "AT+MODE=0")  # 0 = Transparent mode

        # 8. Finale Konfiguration auslesen
        print("\n8. Finale Konfiguration:")
        send_at_command(ser, "AT+CFG?", wait_time=2)

        print("\n" + "="*60)
        print("✓ E22 Konfiguration abgeschlossen!")
        print("="*60)
        print("\nParameter:")
        print(f"  Frequenz:     {FREQ_MHZ} MHz")
        print(f"  SF:           SF{SPREADING_FACTOR}")
        print(f"  Bandwidth:    {BANDWIDTH} kHz")
        print(f"  Power:        {POWER_DBM} dBm")
        print(f"  Address:      {ADDRESS}")
        print(f"  Network ID:   {NETWORK_ID}")
        print(f"  Mode:         Transparent")
        print("\nHinweise:")
        print("  1. Setze M0=0, M1=0 für normalen Betrieb")
        print("  2. Für Test: python3 e22_read.py")
        print("  3. Oder sende: echo 'Test' > /dev/ttyUSB0")

        ser.close()

    except serial.SerialException as e:
        print(f"\n❌ Fehler beim Öffnen von {SERIAL_PORT}: {e}")
        print("\nTipps:")
        print(f"  1. Port verfügbar? ls -l {SERIAL_PORT}")
        print(f"  2. Rechte? sudo chmod 666 {SERIAL_PORT}")
        print(f"  3. Richtiger Port? ls /dev/ttyUSB*")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        sys.exit(1)

def show_help():
    """Zeigt Hilfe an"""
    print("""
E22 Konfiguration für LoRa Repeater Test
=========================================

Verwendung:
    python3 e22_configure_repeater.py

Voraussetzungen:
    1. E22 im AT-Modus (M0=HIGH, M1=HIGH)
    2. USB-Serial Adapter angeschlossen
    3. pyserial installiert: pip3 install pyserial

Parameter (passend zu lorarep.py):
    - Frequenz: 868.1 MHz
    - SF: SF7
    - Bandwidth: 125 kHz
    - Power: 14 dBm
    - Mode: Transparent

Nach der Konfiguration:
    1. M0=LOW, M1=LOW setzen (normaler Modus)
    2. Test mit: python3 e22_read.py
    3. Oder: echo "Test" > /dev/ttyUSB0

Troubleshooting:
    - Keine Antwort? → Prüfe M0/M1 Pins (müssen HIGH sein)
    - Port nicht gefunden? → ls /dev/ttyUSB*
    - Permission denied? → sudo chmod 666 /dev/ttyUSB0
""")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help", "help"]:
        show_help()
    else:
        configure_e22()
