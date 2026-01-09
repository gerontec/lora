#!/usr/bin/python3
"""
E90-DTU Konfigurations-Persistenz Test

Prüft ob die RELAY-Konfiguration nach Power-Cycle erhalten bleibt.
WICHTIG für jahrelangen autarken Betrieb auf dem Berg!

Test-Ablauf:
1. Konfiguration auslesen (vorher)
2. Benutzer schaltet E90-DTU aus und wieder ein
3. Konfiguration erneut auslesen (nachher)
4. Vergleich und Verifizierung

Verwendung:
    python3 e90_persistence_test.py --port /dev/ttyUSB0
"""

import serial
import argparse
import time
import json
import os
from datetime import datetime

DEFAULT_PORT = '/dev/ttyUSB0'
BACKUP_DIR = '/home/user/lora/config_backups'

def send_at_command(ser, command, wait_time=0.5):
    """Sendet AT-Command und gibt Antwort zurück"""
    ser.write(command.encode())
    ser.flush()
    time.sleep(wait_time)

    response = b''
    while ser.in_waiting > 0:
        response += ser.read(ser.in_waiting)
        time.sleep(0.1)

    return response.decode('utf-8', errors='ignore').strip()

def parse_lora_config(response):
    """Parsed AT+LORA Response in strukturierte Daten"""
    # Erwartetes Format: +LORA=65535,18,9600,240,RSCHON,PWMAX,0,RSDATON,TRNOR,RLYON,LBTOFF,WOROFF,2000,0
    if not response.startswith('+LORA='):
        return None

    params_str = response.replace('+LORA=', '')
    params = params_str.split(',')

    if len(params) < 14:
        return None

    config = {
        'addr': params[0],
        'netid': params[1],
        'air_baud': params[2],
        'pack_length': params[3],
        'rssi_en': params[4],
        'tx_pow': params[5],
        'channel': params[6],
        'rssi_data': params[7],
        'tr_mod': params[8],
        'relay': params[9],          # KRITISCH!
        'lbt': params[10],
        'wor': params[11],
        'wor_tim': params[12],
        'crypt': params[13],
        'timestamp': datetime.now().isoformat()
    }

    return config

def save_config_backup(config, filename):
    """Speichert Konfiguration als JSON Backup"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    filepath = os.path.join(BACKUP_DIR, filename)

    with open(filepath, 'w') as f:
        json.dump(config, f, indent=2)

    print(f"✅ Backup gespeichert: {filepath}")
    return filepath

def load_config_backup(filename):
    """Lädt Konfigurations-Backup"""
    filepath = os.path.join(BACKUP_DIR, filename)

    if not os.path.exists(filepath):
        return None

    with open(filepath, 'r') as f:
        return json.load(f)

def compare_configs(config1, config2):
    """Vergleicht zwei Konfigurationen und zeigt Unterschiede"""
    differences = []

    # Timestamp ignorieren beim Vergleich
    keys_to_check = [k for k in config1.keys() if k != 'timestamp']

    for key in keys_to_check:
        val1 = config1.get(key)
        val2 = config2.get(key)

        if val1 != val2:
            differences.append({
                'parameter': key,
                'before': val1,
                'after': val2
            })

    return differences

def print_config(config, title="Konfiguration"):
    """Gibt Konfiguration formatiert aus"""
    print(f"\n{title}:")
    print("=" * 70)

    # Kritische Parameter hervorheben
    critical_params = ['relay', 'tx_pow', 'channel']

    for key, value in config.items():
        if key == 'timestamp':
            continue

        prefix = "⭐⭐⭐" if key in critical_params else "   "
        print(f"{prefix} {key:15} = {value}")

    print("=" * 70)

def test_power_cycle_persistence(ser):
    """Testet Persistenz nach Power-Cycle"""
    print("\n" + "=" * 70)
    print("  PERSISTENZ-TEST: Power-Cycle")
    print("=" * 70)

    # Schritt 1: Aktuelle Konfiguration auslesen
    print("\n📖 Schritt 1: Aktuelle Konfiguration auslesen...")
    response = send_at_command(ser, "AT+LORA\r\n", wait_time=1.0)
    config_before = parse_lora_config(response)

    if not config_before:
        print("❌ Fehler beim Auslesen der Konfiguration!")
        return False

    print_config(config_before, "Konfiguration VORHER")

    # Backup speichern
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"e90_config_before_{timestamp}.json"
    save_config_backup(config_before, backup_file)

    # Schritt 2: Benutzer auffordern, Power-Cycle durchzuführen
    print("\n" + "=" * 70)
    print("⚡ Schritt 2: POWER-CYCLE durchführen")
    print("=" * 70)
    print("\n  Bitte:")
    print("  1. E90-DTU Stromversorgung AUSSCHALTEN (8-28V trennen)")
    print("  2. 10 Sekunden warten")
    print("  3. E90-DTU wieder EINSCHALTEN")
    print("  4. 5 Sekunden warten bis Boot abgeschlossen")
    print()
    input("  Drücke ENTER wenn Power-Cycle abgeschlossen ist...")

    # Schritt 3: Serielle Verbindung neu aufbauen
    print("\n🔄 Schritt 3: Verbindung neu aufbauen...")
    ser.close()
    time.sleep(2)

    try:
        ser.open()
        time.sleep(0.5)
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        print("✅ Verbindung wiederhergestellt")
    except serial.SerialException as e:
        print(f"❌ Fehler beim Neuverbinden: {e}")
        return False

    # Schritt 4: Konfiguration erneut auslesen
    print("\n📖 Schritt 4: Konfiguration nach Power-Cycle auslesen...")
    time.sleep(1)  # Device stabilisieren lassen

    response = send_at_command(ser, "AT+LORA\r\n", wait_time=1.0)
    config_after = parse_lora_config(response)

    if not config_after:
        print("❌ Fehler beim Auslesen der Konfiguration nach Power-Cycle!")
        return False

    print_config(config_after, "Konfiguration NACHHER")

    # Backup speichern
    backup_file_after = f"e90_config_after_{timestamp}.json"
    save_config_backup(config_after, backup_file_after)

    # Schritt 5: Vergleich
    print("\n🔍 Schritt 5: Vergleich...")
    differences = compare_configs(config_before, config_after)

    if not differences:
        print("✅✅✅ PERFEKT! Konfiguration ist 100% PERSISTENT! ✅✅✅")
        print("\n   Alle Parameter sind nach Power-Cycle identisch!")
        print("   → E90-DTU kann jahrelang autark auf dem Berg laufen!")
        return True
    else:
        print("⚠️⚠️⚠️ WARNUNG! Konfiguration hat sich geändert! ⚠️⚠️⚠️")
        print("\n   Unterschiede gefunden:")
        for diff in differences:
            print(f"   - {diff['parameter']:15}: {diff['before']} → {diff['after']}")

        # Kritische Parameter prüfen
        critical_changed = [d for d in differences if d['parameter'] in ['relay', 'tx_pow', 'channel']]

        if critical_changed:
            print("\n❌ KRITISCH! Folgende wichtige Parameter haben sich geändert:")
            for diff in critical_changed:
                print(f"   ⚠️  {diff['parameter']}: {diff['before']} → {diff['after']}")
            print("\n   → E90-DTU ist NICHT geeignet für autarken Betrieb!")
            print("   → Alternative Lösung erforderlich!")
        else:
            print("\n⚠️  Nur unkritische Parameter geändert")
            print("   → Kann eventuell toleriert werden")

        return False

def test_multiple_power_cycles(ser, cycles=3):
    """Testet Persistenz über mehrere Power-Cycles"""
    print("\n" + "=" * 70)
    print(f"  STRESS-TEST: {cycles} Power-Cycles")
    print("=" * 70)

    configs = []

    for i in range(cycles):
        print(f"\n🔄 Power-Cycle {i+1}/{cycles}")
        print("-" * 70)

        response = send_at_command(ser, "AT+LORA\r\n", wait_time=1.0)
        config = parse_lora_config(response)

        if config:
            configs.append(config)
            print(f"✅ Config {i+1} ausgelesen")

        if i < cycles - 1:
            print("\n⚡ Bitte Power-Cycle durchführen...")
            input("   Drücke ENTER wenn fertig...")

            ser.close()
            time.sleep(2)
            ser.open()
            time.sleep(0.5)
            ser.reset_input_buffer()

    # Alle Configs vergleichen
    print("\n🔍 Vergleiche alle Konfigurationen...")
    all_identical = True

    for i in range(1, len(configs)):
        diffs = compare_configs(configs[0], configs[i])
        if diffs:
            print(f"⚠️  Config 1 vs Config {i+1}: {len(diffs)} Unterschiede")
            all_identical = False

    if all_identical:
        print("✅ Alle Konfigurationen sind identisch über alle Power-Cycles!")
        return True
    else:
        print("❌ Konfigurationen sind NICHT konsistent!")
        return False

def generate_restore_script(config):
    """Generiert Restore-Skript aus Backup"""
    script_lines = [
        "#!/bin/bash",
        "# E90-DTU Konfigurations-Restore Skript",
        f"# Erstellt: {datetime.now().isoformat()}",
        "",
        "python3 e90_repeater_setup.py \\",
        "  --mode repeater \\",
        f"  --addr {config['addr']} \\",
        f"  --netid {config['netid']} \\",
        f"  --channel {config['channel']} \\",
        f"  --air-baud {config['air_baud']} \\",
        f"  --tx-pow {config['tx_pow']}",
        ""
    ]

    script_path = os.path.join(BACKUP_DIR, 'restore_config.sh')
    with open(script_path, 'w') as f:
        f.write('\n'.join(script_lines))

    os.chmod(script_path, 0o755)
    print(f"✅ Restore-Skript erstellt: {script_path}")

def main():
    parser = argparse.ArgumentParser(
        description="E90-DTU Konfigurations-Persistenz Test",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--port', default=DEFAULT_PORT, help='Serieller Port')
    parser.add_argument('--test', choices=['single', 'stress'], default='single',
                       help='Test-Modus (single=1×, stress=3×)')
    parser.add_argument('--cycles', type=int, default=3, help='Anzahl Power-Cycles für Stress-Test')

    args = parser.parse_args()

    try:
        print("=" * 70)
        print("  E90-DTU PERSISTENZ-TEST")
        print("  Prüft ob Konfiguration nach Power-Cycle erhalten bleibt")
        print("=" * 70)

        ser = serial.Serial(
            port=args.port,
            baudrate=9600,
            timeout=2
        )

        time.sleep(0.5)
        ser.reset_input_buffer()

        if args.test == 'single':
            success = test_power_cycle_persistence(ser)
        else:
            success = test_multiple_power_cycles(ser, args.cycles)

        # Aktuelles Config-Backup und Restore-Skript erstellen
        print("\n📦 Erstelle Backup und Restore-Skript...")
        response = send_at_command(ser, "AT+LORA\r\n", wait_time=1.0)
        config = parse_lora_config(response)

        if config:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_config_backup(config, f"e90_config_{timestamp}.json")
            generate_restore_script(config)

        ser.close()

        # Zusammenfassung
        print("\n" + "=" * 70)
        if success:
            print("✅ ERGEBNIS: E90-DTU Konfiguration ist PERSISTENT")
            print("   → Geeignet für jahrelangen autarken Betrieb!")
        else:
            print("❌ ERGEBNIS: E90-DTU Konfiguration ist NICHT PERSISTENT")
            print("   → NICHT geeignet für autarken Betrieb ohne Watchdog!")
        print("=" * 70)

        # Empfehlungen
        print("\n📋 Empfehlungen:")
        if success:
            print("  1. Backup-Datei sicher aufbewahren")
            print("  2. Restore-Skript testen vor Deployment")
            print("  3. Jährliche Wartung: Config verifizieren")
        else:
            print("  1. Watchdog-System implementieren (siehe E90_DTU_GUIDE.md)")
            print("  2. Remote-Monitoring einrichten")
            print("  3. Automatisches Config-Restore bei Boot")
            print("  4. Alternative Hardware erwägen (z.B. ESP32 + rf95modem)")

    except serial.SerialException as e:
        print(f"\n❌ Serieller Fehler: {e}")
    except KeyboardInterrupt:
        print("\n\n⚠️ Test abgebrochen")
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
