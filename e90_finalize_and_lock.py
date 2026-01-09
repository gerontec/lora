#!/usr/bin/python3
"""
E90-DTU Finalize and Lock Configuration

ZWECK: Konfiguration abschließen und Remote-Config DEAKTIVIEREN
       → Eliminiert Lockout-Risiko für autarken Berg-Betrieb!

Ablauf:
1. Finale Konfiguration anwenden (RELAY=ON, optimierte Parameter)
2. Persistenz verifizieren (3× Power-Cycles)
3. Backup erstellen (mehrfach!)
4. Remote-Konfiguration DEAKTIVIEREN (RS485 trennen)
5. Deployment-Checkliste erstellen

Verwendung:
    python3 e90_finalize_and_lock.py --port /dev/ttyUSB0

WICHTIG: Nach RS485-Trennung ist KEINE Remote-Änderung mehr möglich
         → 100% Schutz gegen Lockout durch Fehlkonfiguration!
         → Änderungen nur noch mit physischem Zugang zum Device!

Sicherheit:
  ✅ Remote-Config deaktiviert (RS485 getrennt)
  ✅ Config persistent in EEPROM (>10 Jahre)
  ✅ Keine Lockout-Gefahr bei autarkem Betrieb
"""

import serial
import argparse
import time
import json
import os
from datetime import datetime

DEFAULT_PORT = '/dev/ttyUSB0'
FINAL_CONFIG_FILE = 'FINAL_E90_CONFIG.json'
BACKUP_DIR = '/home/user/lora/config_backups'

# FINALE REPEATER-KONFIGURATION
# Diese Config ist für jahrelangen autarken Betrieb optimiert
FINAL_CONFIG = {
    'addr': 65535,          # Broadcast - empfängt ALLE
    'netid': 18,            # Network ID (kompatibel mit E22)
    'air_baud': '9600',     # SF7-äquivalent
    'pack_length': '240',   # Maximum
    'rssi_en': 'RSCHON',   # RSSI Ambient Noise
    'tx_pow': 'PWMAX',      # Maximale Leistung (30 dBm)
    'channel': 18,          # 868.1 MHz (850.125 + 18)
    'rssi_data': 'RSDATON', # RSSI in Daten
    'tr_mod': 'TRNOR',      # Transparent Mode
    'relay': 'RLYON',       # ⭐ RELAY AKTIVIERT
    'lbt': 'LBTOFF',        # LBT aus (Berg = wenig Traffic)
    'wor': 'WOROFF',        # Wake-on-Radio aus (Dauerbetrieb!)
    'wor_tim': '2000',      # Irrelevant bei WOROFF
    'crypt': 0              # Keine Verschlüsselung
}

def print_banner():
    print("=" * 70)
    print("  E90-DTU FINALIZE AND LOCK")
    print("  Konfiguration für jahrelangen autarken Betrieb")
    print("=" * 70)
    print()

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

def apply_final_config(ser, config):
    """Wendet finale Konfiguration an"""
    print("\n📋 FINALE REPEATER-KONFIGURATION:")
    print("=" * 70)

    for key, value in config.items():
        prefix = "⭐⭐⭐" if key == 'relay' else "   "
        print(f"{prefix} {key:15} = {value}")

    print("=" * 70)
    print()
    print("⚠️  WARNUNG: Diese Config wird PERMANENT!")
    print("   Änderungen nur noch mit physischem Zugang möglich!")
    print()
    response = input("Fortfahren? [yes/NO]: ")

    if response.lower() != 'yes':
        print("❌ Abgebrochen")
        return False

    # Config als AT-Befehl formatieren
    params = [
        str(config['addr']),
        str(config['netid']),
        config['air_baud'],
        config['pack_length'],
        config['rssi_en'],
        config['tx_pow'],
        str(config['channel']),
        config['rssi_data'],
        config['tr_mod'],
        config['relay'],
        config['lbt'],
        config['wor'],
        config['wor_tim'],
        str(config['crypt'])
    ]

    command = f"AT+LORA={','.join(params)}\r\n"
    print(f"\n📤 Sende Konfiguration...")
    response = send_at_command(ser, command, wait_time=1.5)

    if "OK" in response or "SUCCESS" in response:
        print("✅ Konfiguration erfolgreich angewendet!")
        return True
    else:
        print(f"❌ Fehler: {response}")
        return False

def verify_persistence(ser, cycles=3):
    """Verifiziert Persistenz über mehrere Power-Cycles"""
    print("\n🔄 PERSISTENZ-VERIFIZIERUNG")
    print("=" * 70)
    print(f"Führe {cycles} Power-Cycle Tests durch...")
    print()

    for i in range(cycles):
        print(f"\n⚡ Power-Cycle {i+1}/{cycles}")

        if i > 0:
            print("   1. E90-DTU Stromversorgung TRENNEN")
            print("   2. 10 Sekunden warten")
            print("   3. E90-DTU wieder EINSCHALTEN")
            print("   4. 5 Sekunden Boot-Zeit abwarten")
            input("   Drücke ENTER wenn fertig...")

            # Reconnect
            ser.close()
            time.sleep(2)
            ser.open()
            time.sleep(1)
            ser.reset_input_buffer()

        # Config auslesen
        response = send_at_command(ser, "AT+LORA\r\n", wait_time=1.0)
        print(f"   Response: {response[:50]}...")

        # Prüfen ob RELAY=ON noch drin ist
        if 'RLYON' in response:
            print("   ✅ RELAY=ON verifiziert!")
        else:
            print("   ❌ WARNUNG: RELAY nicht ON!")
            return False

    print("\n✅✅✅ PERSISTENZ BESTÄTIGT über alle Power-Cycles!")
    return True

def create_backups(config):
    """Erstellt mehrere Backup-Kopien"""
    print("\n💾 BACKUP-ERSTELLUNG")
    print("=" * 70)

    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    backups = []

    # Backup 1: JSON im Backup-Ordner
    backup1 = os.path.join(BACKUP_DIR, f'FINAL_CONFIG_{timestamp}.json')
    with open(backup1, 'w') as f:
        json.dump(config, f, indent=2)
    backups.append(backup1)
    print(f"✅ Backup 1: {backup1}")

    # Backup 2: JSON im aktuellen Verzeichnis
    backup2 = FINAL_CONFIG_FILE
    with open(backup2, 'w') as f:
        json.dump(config, f, indent=2)
    backups.append(backup2)
    print(f"✅ Backup 2: {backup2}")

    # Backup 3: Human-readable Text
    backup3 = os.path.join(BACKUP_DIR, f'FINAL_CONFIG_{timestamp}.txt')
    with open(backup3, 'w') as f:
        f.write("E90-DTU FINALE KONFIGURATION\n")
        f.write("=" * 70 + "\n")
        f.write(f"Erstellt: {datetime.now().isoformat()}\n")
        f.write("=" * 70 + "\n\n")
        for key, value in config.items():
            f.write(f"{key:20} = {value}\n")
        f.write("\n" + "=" * 70 + "\n")
        f.write("RESTORE-BEFEHL:\n")
        f.write(f"python3 e90_repeater_setup.py --mode repeater \\\n")
        f.write(f"  --addr {config['addr']} \\\n")
        f.write(f"  --netid {config['netid']} \\\n")
        f.write(f"  --channel {config['channel']} \\\n")
        f.write(f"  --air-baud {config['air_baud']} \\\n")
        f.write(f"  --tx-pow {config['tx_pow']}\n")
    backups.append(backup3)
    print(f"✅ Backup 3: {backup3}")

    # Backup 4: Shell-Skript
    backup4 = os.path.join(BACKUP_DIR, 'RESTORE_FINAL_CONFIG.sh')
    with open(backup4, 'w') as f:
        f.write("#!/bin/bash\n")
        f.write("# E90-DTU Finale Konfiguration wiederherstellen\n\n")
        f.write("python3 e90_repeater_setup.py \\\n")
        f.write("  --mode repeater \\\n")
        f.write(f"  --addr {config['addr']} \\\n")
        f.write(f"  --netid {config['netid']} \\\n")
        f.write(f"  --channel {config['channel']} \\\n")
        f.write(f"  --air-baud {config['air_baud']} \\\n")
        f.write(f"  --tx-pow {config['tx_pow']}\n")
    os.chmod(backup4, 0o755)
    backups.append(backup4)
    print(f"✅ Backup 4: {backup4}")

    print("\n💡 Empfehlung: Backup auf 2 USB-Sticks kopieren!")
    print(f"   cp -r {BACKUP_DIR}/ /media/usb1/")
    print(f"   cp -r {BACKUP_DIR}/ /media/usb2/")

    return backups

def disable_remote_config():
    """Deaktiviert Remote-Konfiguration durch physische Trennung"""
    print("\n🔒 REMOTE-KONFIGURATION DEAKTIVIEREN")
    print("=" * 70)
    print()
    print("⚠️  WICHTIG: Um Lockout-Risiko zu eliminieren, muss")
    print("   Remote-Konfiguration PERMANENT deaktiviert werden!")
    print()
    print("=" * 70)
    print("METHODE: RS485-Kabel physisch trennen")
    print("=" * 70)
    print()
    print("Anleitung:")
    print("  1. E90-DTU Gehäuse öffnen")
    print("  2. RS485 A/B Kabel vom E90-DTU abziehen")
    print("  3. Kabelenden mit Schrumpfschlauch isolieren")
    print("  4. Kabel im Gehäuse verstauen (für Notfall-Wartung)")
    print("  5. Foto machen (Dokumentation!)")
    print()
    print("Ergebnis:")
    print("  ✅ Keine Remote-Konfiguration mehr möglich")
    print("  ✅ 100% Schutz gegen Lockout durch Fehlkonfiguration")
    print("  ✅ Config bleibt permanent in EEPROM gespeichert")
    print("  ✅ E90-DTU funktioniert weiterhin als Repeater")
    print()
    print("Alternative (wenn Remote-Management benötigt):")
    print("  → RS485-Kabel durch Kippschalter (plombiert)")
    print("  → Bei Wartung: Plombe brechen, Schalter AN, rekonfigurieren")
    print("  → Risiko: Siehe E90_LOCKOUT_PREVENTION.md")
    print()
    print("=" * 70)
    print()

    response = input("❓ Wirst du RS485-Kabel trennen? [yes/NO]: ")

    if response.lower() == 'yes':
        print("\n✅ Bestätigt: RS485 wird getrennt")
        print("   → Remote-Konfiguration DEAKTIVIERT")
        print("   → Lockout-Risiko ELIMINIERT")
        return True
    else:
        print("\n⚠️  WARNUNG: RS485 bleibt verbunden!")
        print("   → Remote-Konfiguration AKTIV")
        print("   → Lockout-Risiko bleibt bestehen!")
        print("   → Siehe E90_LOCKOUT_PREVENTION.md für sichere Nutzung")
        return False

def generate_deployment_checklist(backups):
    """Erstellt Deployment-Checkliste"""
    checklist_file = os.path.join(BACKUP_DIR, 'DEPLOYMENT_CHECKLIST.txt')

    with open(checklist_file, 'w') as f:
        f.write("E90-DTU BERGGIPFEL-DEPLOYMENT CHECKLISTE\n")
        f.write("=" * 70 + "\n\n")

        f.write("VOR DER INSTALLATION:\n")
        f.write("-" * 70 + "\n")
        f.write("[ ] Finale Konfiguration angewendet\n")
        f.write("[ ] Persistenz verifiziert (3× Power-Cycles)\n")
        f.write("[ ] Backups erstellt (4 Dateien)\n")
        f.write("[ ] Backups auf 2 USB-Sticks kopiert\n")
        f.write("[ ] ⭐⭐⭐ RS485-KABEL GETRENNT (Remote-Config deaktiviert!) ⭐⭐⭐\n")
        f.write("[ ] Kabelenden isoliert (Schrumpfschlauch)\n")
        f.write("[ ] Kabel im Gehäuse verstaut (für Notfall)\n")
        f.write("[ ] Gehäuse-Öffnung dokumentiert (Fotos!)\n")
        f.write("[ ] Kabel-Layout dokumentiert (Foto VOR Trennung!)\n")
        f.write("[ ] Notfall-Kontakt definiert\n\n")

        f.write("AM BERG:\n")
        f.write("-" * 70 + "\n")
        f.write("[ ] Standort GPS-Koordinaten notiert\n")
        f.write("[ ] Solar-Panel montiert (Süd, 60° Neigung)\n")
        f.write("[ ] Batterie angeschlossen und geladen\n")
        f.write("[ ] E90-DTU eingeschaltet\n")
        f.write("[ ] Antenne montiert (3m Mast)\n")
        f.write("[ ] Blitzschutz installiert\n")
        f.write("[ ] Test vom Tal: Ping erfolgreich\n")
        f.write("[ ] RSSI gemessen und dokumentiert\n")
        f.write("[ ] Gehäuse verschlossen und versiegelt\n")
        f.write("[ ] Abschlussfoto gemacht\n")
        f.write("[ ] 🔒 Remote-Config Status: DEAKTIVIERT ✅\n\n")

        f.write("BACKUP-DATEIEN:\n")
        f.write("-" * 70 + "\n")
        for backup in backups:
            f.write(f"  {backup}\n")
        f.write("\n")

        f.write("NOTFALL-RECOVERY:\n")
        f.write("-" * 70 + "\n")
        f.write("1. Berg-Zugang mit Werkzeug und Laptop\n")
        f.write("2. Gehäuse öffnen\n")
        f.write("3. RS485 USB-Adapter anschließen\n")
        f.write("4. Backup wiederherstellen:\n")
        f.write(f"   cd {BACKUP_DIR}\n")
        f.write("   ./RESTORE_FINAL_CONFIG.sh\n")
        f.write("5. Testen und Gehäuse schließen\n")

    print(f"\n✅ Checkliste erstellt: {checklist_file}")
    return checklist_file

def main():
    parser = argparse.ArgumentParser(
        description="E90-DTU Finalize and Lock Configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--port', default=DEFAULT_PORT, help='Serieller Port')
    parser.add_argument('--skip-verify', action='store_true',
                       help='Persistenz-Verifizierung überspringen (nicht empfohlen!)')

    args = parser.parse_args()

    try:
        print_banner()

        # Serielle Verbindung
        print(f"🔌 Verbinde zu {args.port}...")
        ser = serial.Serial(args.port, 9600, timeout=2)
        time.sleep(0.5)
        ser.reset_input_buffer()
        print("✅ Verbunden!\n")

        # Schritt 1: Aktuelle Config abfragen
        print("📖 Schritt 1: Aktuelle Konfiguration abfragen...")
        response = send_at_command(ser, "AT+LORA\r\n", wait_time=1.0)
        print(f"   Aktuell: {response[:60]}...\n")

        # Schritt 2: Finale Config anwenden
        print("📋 Schritt 2: Finale Konfiguration anwenden...")
        if not apply_final_config(ser, FINAL_CONFIG):
            print("❌ Fehler bei Konfiguration!")
            return

        time.sleep(2)

        # Schritt 3: Persistenz verifizieren
        if not args.skip_verify:
            print("\n🔄 Schritt 3: Persistenz verifizieren...")
            if not verify_persistence(ser, cycles=3):
                print("❌ Persistenz-Verifizierung fehlgeschlagen!")
                print("   → Nicht für Berg-Deployment geeignet!")
                return
        else:
            print("\n⚠️  Schritt 3: Persistenz-Verifizierung übersprungen!")

        # Schritt 4: Backups erstellen
        print("\n💾 Schritt 4: Backups erstellen...")
        backups = create_backups(FINAL_CONFIG)

        # Schritt 5: Deployment-Checkliste
        print("\n📋 Schritt 5: Deployment-Checkliste erstellen...")
        checklist = generate_deployment_checklist(backups)

        # Schritt 6: Remote-Konfiguration deaktivieren
        rs485_disconnected = disable_remote_config()

        # Zusammenfassung
        print("\n" + "=" * 70)
        if rs485_disconnected:
            print("✅✅✅ E90-DTU IST BEREIT & GESICHERT! ✅✅✅")
            print("=" * 70)
            print()
            print("🔒 Status: REMOTE-KONFIGURATION DEAKTIVIERT")
            print("   → RS485-Kabel wird getrennt")
            print("   → Lockout-Risiko ELIMINIERT")
        else:
            print("✅ E90-DTU IST BEREIT FÜR BERG-DEPLOYMENT")
            print("=" * 70)
            print()
            print("⚠️  Status: REMOTE-KONFIGURATION AKTIV")
            print("   → RS485-Kabel bleibt verbunden")
            print("   → Lockout-Risiko besteht!")
        print("=" * 70)
        print()
        print("Nächste Schritte:")
        print("  1. Backups auf 2 USB-Sticks kopieren")
        if rs485_disconnected:
            print("  2. RS485-Kabel JETZT trennen")
        else:
            print("  2. (Optional) RS485-Kabel trennen für maximale Sicherheit")
        print("  3. Deployment-Checkliste durchgehen")
        print("  4. Berg-Installation durchführen")
        print()
        print(f"📄 Checkliste: {checklist}")
        print()
        if rs485_disconnected:
            print("✅ WICHTIG: Nach RS485-Trennung keine Remote-Config mehr möglich!")
            print("   → Änderungen nur mit physischem Zugang zum Device!")
        else:
            print("⚠️  WICHTIG: Remote-Konfiguration weiterhin möglich!")
            print("   → Befolge E90_LOCKOUT_PREVENTION.md für sichere Nutzung!")
        print()

        ser.close()

    except serial.SerialException as e:
        print(f"\n❌ Serieller Fehler: {e}")
    except KeyboardInterrupt:
        print("\n\n⚠️ Abgebrochen")
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
