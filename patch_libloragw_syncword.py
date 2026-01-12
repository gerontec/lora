#!/usr/bin/env python3
"""
Patch libloragw.so Binary für Custom Sync Word

Warnung: Dies ist Binary-Patching und kann die Library beschädigen!
         Nutze nur wenn Source Code Patch nicht möglich ist.

Usage:
    scp patch_libloragw_syncword.py root@10.0.0.2:/tmp/
    ssh root@10.0.0.2 "python3 /tmp/patch_libloragw_syncword.py 0x11"

LoRa Sync Word Format (16-bit):
    0x1424 → Private (MSB=0x14, LSB=0x24) → Wird zu 0x12
    0x3444 → Public  (MSB=0x34, LSB=0x44) → Wird zu 0x34
    0x11XX → Custom  (MSB=0x11, LSB=0xXX)
"""

import sys
import shutil
import os

LIBLORAGW_PATH = "/usr/lib/libloragw.so"

def find_and_replace(data, old_pattern, new_pattern, description):
    """Finde und ersetze Pattern im Binary"""
    count = data.count(old_pattern)

    if count == 0:
        return data, 0

    print(f"  Found {count} occurrence(s) of {description}")
    print(f"    Old: {old_pattern.hex()}")
    print(f"    New: {new_pattern.hex()}")

    data = data.replace(old_pattern, new_pattern)
    return data, count

def patch_syncword(new_sync):
    """Patche libloragw.so mit neuem Sync Word"""

    if not os.path.exists(LIBLORAGW_PATH):
        print(f"ERROR: {LIBLORAGW_PATH} not found!")
        return False

    print("╔════════════════════════════════════════════════════════╗")
    print("║  libloragw.so - Binary Sync Word Patch                ║")
    print("╚════════════════════════════════════════════════════════╝")
    print()
    print(f"Target Library: {LIBLORAGW_PATH}")
    print(f"New Sync Word:  0x{new_sync:02X}")
    print()

    # Lese Binary
    print("1. Reading binary...")
    try:
        with open(LIBLORAGW_PATH, "rb") as f:
            data = bytearray(f.read())
    except Exception as e:
        print(f"ERROR: Failed to read library: {e}")
        return False

    print(f"   ✓ Size: {len(data)} bytes")
    print()

    # Backup erstellen
    backup_path = LIBLORAGW_PATH + ".backup"
    print(f"2. Creating backup: {backup_path}")
    try:
        shutil.copy(LIBLORAGW_PATH, backup_path)
        print("   ✓ Backup created")
    except Exception as e:
        print(f"ERROR: Failed to create backup: {e}")
        return False
    print()

    # Pattern für LoRa Sync Word
    # SX126x speichert Sync Word als 16-bit Wert
    # Private: 0x1424 (wird interpretiert als 0x12)
    # Public:  0x3444 (wird interpretiert als 0x34)

    print("3. Patching Sync Word patterns...")

    # Pattern 1: Private Sync Word (0x14 0x24)
    old_private = bytes([0x14, 0x24])
    new_custom = bytes([new_sync, 0x44])  # Behalte LSB=0x44

    data, count1 = find_and_replace(
        data, old_private, new_custom,
        "Private Sync Word (0x1424)"
    )

    # Pattern 2: Manchmal als separate Bytes gespeichert
    # Suche nach 0x12 in Nähe von LoRa-Settings
    # (Dies ist spekulativ und kann falsch-positive haben)

    total_changes = count1
    print()

    if total_changes == 0:
        print("⚠️  WARNING: No sync word patterns found!")
        print("   This library may:")
        print("   - Use different encoding")
        print("   - Already be patched")
        print("   - Require source code modification")
        print()
        return False

    print(f"   Total patterns replaced: {total_changes}")
    print()

    # Schreibe gepatchte Version
    print("4. Writing patched library...")
    try:
        with open(LIBLORAGW_PATH, "wb") as f:
            f.write(data)
        print("   ✓ Library patched")
    except Exception as e:
        print(f"ERROR: Failed to write library: {e}")
        print(f"   Restoring backup...")
        shutil.copy(backup_path, LIBLORAGW_PATH)
        return False
    print()

    print("════════════════════════════════════════════════════════")
    print(f"✅ Successfully patched to Sync Word 0x{new_sync:02X}")
    print()
    print("Next steps:")
    print("  1. Set lorawan_public=false:")
    print("     uci set lora.@lora[0].lorawan_public=0")
    print("     uci commit lora")
    print()
    print("  2. Restart gateway:")
    print("     /etc/init.d/lora-gateway restart")
    print()
    print("To restore:")
    print(f"  cp {backup_path} {LIBLORAGW_PATH}")
    print("  /etc/init.d/lora-gateway restart")
    print("════════════════════════════════════════════════════════")

    return True

def main():
    if len(sys.argv) != 2:
        print("Usage: patch_libloragw_syncword.py <sync_word>")
        print()
        print("Examples:")
        print("  patch_libloragw_syncword.py 0x11   # Custom sync word")
        print("  patch_libloragw_syncword.py 0x12   # LoRa Private (default)")
        print("  patch_libloragw_syncword.py 0x34   # LoRaWAN Public")
        print()
        print("⚠️  WARNING: This patches a system library!")
        print("   Create backup before running.")
        return 1

    try:
        sync_word = int(sys.argv[1], 0)
    except ValueError:
        print(f"ERROR: Invalid sync word: {sys.argv[1]}")
        print("Must be hex (0x11) or decimal (17)")
        return 1

    if sync_word < 0 or sync_word > 255:
        print(f"ERROR: Sync word must be 0x00-0xFF, got 0x{sync_word:02X}")
        return 1

    print()
    print("⚠️  WARNING: Binary patching is risky!")
    print("   This will modify a system library.")
    print()
    response = input("Continue? [y/N]: ")
    if response.lower() != 'y':
        print("Aborted.")
        return 0

    print()

    if patch_syncword(sync_word):
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())
