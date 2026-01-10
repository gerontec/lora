#!/usr/bin/python3
"""
E90-DTU TCP Configuration Reader

Connects to E90-DTU via TCP/IP and reads the current configuration.
The E90-DTU (Ethernet version) listens on port 8886 for configuration commands.

Usage:
    python3 gete90conf.py
    python3 gete90conf.py --ip 192.168.4.101 --port 8886
    python3 gete90conf.py --timeout 10
"""

import socket
import argparse
import sys
import time

# Default connection parameters
DEFAULT_IP = '192.168.4.101'
DEFAULT_PORT = 8886
DEFAULT_TIMEOUT = 5  # seconds
BUFFER_SIZE = 1024

def send_hex_command(sock, hex_string):
    """
    Sends a hex command string to the socket.
    hex_string should be like "C10009" (without 0x prefix or spaces)
    """
    try:
        # Remove any spaces or 0x prefixes
        hex_string = hex_string.replace(' ', '').replace('0x', '').replace('0X', '')

        # Convert hex string to bytes
        command_bytes = bytes.fromhex(hex_string)

        print(f"Sende Abfrage-Befehl: {hex_string}")
        sock.send(command_bytes)

        return True
    except ValueError as e:
        print(f"Fehler: Ungültiges Hex-Format: {e}")
        return False

def receive_response(sock, timeout=None):
    """
    Receives response from the socket with optional timeout.
    """
    if timeout:
        sock.settimeout(timeout)

    try:
        response = sock.recv(BUFFER_SIZE)
        if response:
            return response
        else:
            print("Warnung: Leere Antwort empfangen")
            return None
    except socket.timeout:
        print(f"Fehler: Zeitüberschreitung ({timeout}s) - Keine Antwort vom Gerät")
        return None
    except Exception as e:
        print(f"Fehler beim Empfangen: {e}")
        return None

def parse_response(response):
    """
    Parses the response from E90-DTU configuration query.
    """
    if not response:
        return None

    print("\n=== Rohe Antwort ===")
    print(f"Hex: {response.hex().upper()}")

    # Try to decode as ASCII/UTF-8
    try:
        decoded = response.decode('utf-8', errors='ignore').strip()
        if decoded:
            print(f"Text: {decoded}")
    except:
        pass

    print("=" * 50)

    # If response starts with 0xC1 (configuration response)
    if len(response) > 0 and response[0] == 0xC1:
        print("\nKonfigurations-Antwort erkannt (0xC1)")

        # Parse configuration bytes
        # This is device-specific - you may need to adjust based on actual protocol
        if len(response) >= 10:
            print("\nParameter (Beispiel-Dekodierung):")
            print(f"  Header: 0x{response[0]:02X}")
            print(f"  Länge: {len(response)} bytes")

            # Print all bytes
            for i, byte in enumerate(response):
                print(f"  Byte {i}: 0x{byte:02X} ({byte})")

    return response

def query_configuration(ip, port, timeout, command="C10009"):
    """
    Connects to E90-DTU and queries configuration.
    """
    sock = None
    try:
        # Create TCP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Set connection timeout
        sock.settimeout(timeout)

        print(f"Verbinde zu {ip}:{port}...")
        sock.connect((ip, port))
        print(f"✅ Verbunden!")

        # Send query command
        if not send_hex_command(sock, command):
            return False

        # Wait a bit for device to process
        time.sleep(0.2)

        # Receive response
        response = receive_response(sock, timeout=timeout)

        if response:
            print("✅ Antwort empfangen!")
            parse_response(response)
            return True
        else:
            print("❌ Keine Antwort empfangen")
            return False

    except socket.timeout:
        print(f"Fehler: Verbindungs-Timeout ({timeout}s)")
        print("\nMögliche Ursachen:")
        print("  1. E90-DTU ist nicht erreichbar (IP/Port prüfen)")
        print("  2. Firewall blockiert Verbindung")
        print("  3. Gerät ist ausgeschaltet oder nicht im Netzwerk")
        print("\nTipps:")
        print(f"  - Ping testen: ping {ip}")
        print(f"  - Port prüfen: nc -zv {ip} {port}")
        print("  - Timeout erhöhen: --timeout 10")
        return False

    except ConnectionRefusedError:
        print(f"Fehler: Verbindung abgelehnt")
        print(f"\nDas Gerät {ip}:{port} verweigert die Verbindung.")
        print("Mögliche Ursachen:")
        print("  1. Falscher Port (Standard ist 8886)")
        print("  2. Dienst läuft nicht auf dem Gerät")
        print("  3. Gerät ist in anderem Modus")
        return False

    except OSError as e:
        if "Network is unreachable" in str(e):
            print(f"Fehler: Netzwerk nicht erreichbar")
            print(f"\n{ip} ist nicht im gleichen Netzwerk.")
            print("Prüfe:")
            print("  - Ist dein Computer im gleichen Netzwerk?")
            print("  - IP-Adresse korrekt?")
            print("  - Netzwerkverbindung aktiv?")
        else:
            print(f"Fehler: {e}")
        return False

    except Exception as e:
        print(f"Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if sock:
            sock.close()
            print("\n🔌 Verbindung geschlossen")

def main():
    parser = argparse.ArgumentParser(
        description="E90-DTU TCP Configuration Reader",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Standard-Abfrage:
  %(prog)s

  # Andere IP-Adresse:
  %(prog)s --ip 192.168.1.100

  # Längerer Timeout:
  %(prog)s --timeout 10

  # Anderer Befehl:
  %(prog)s --command C10009

  # AT-Befehle (für kompatible Geräte):
  %(prog)s --at-mode --command "AT+LORA"
        """
    )

    parser.add_argument('--ip', default=DEFAULT_IP,
                       help=f'IP-Adresse des E90-DTU (Standard: {DEFAULT_IP})')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT,
                       help=f'TCP-Port (Standard: {DEFAULT_PORT})')
    parser.add_argument('--timeout', type=float, default=DEFAULT_TIMEOUT,
                       help=f'Timeout in Sekunden (Standard: {DEFAULT_TIMEOUT})')
    parser.add_argument('--command', default='C10009',
                       help='Hex-Befehl zum Senden (Standard: C10009)')
    parser.add_argument('--at-mode', action='store_true',
                       help='AT-Befehls-Modus (sendet Text statt Hex)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Ausführliche Ausgabe')

    args = parser.parse_args()

    print("=" * 60)
    print("  E90-DTU TCP Konfigurations-Abfrage")
    print("=" * 60)
    print()

    if args.at_mode:
        # AT command mode - send as text
        print("Modus: AT-Befehle")
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(args.timeout)

            print(f"Verbinde zu {args.ip}:{args.port}...")
            sock.connect((args.ip, args.port))
            print("✅ Verbunden!")

            # Send AT command
            command = args.command
            if not command.endswith('\r\n'):
                command += '\r\n'

            print(f"Sende AT-Befehl: {command.strip()}")
            sock.send(command.encode())

            # Receive response
            time.sleep(0.2)
            response = sock.recv(BUFFER_SIZE)

            if response:
                print("\n✅ Antwort:")
                print(response.decode('utf-8', errors='ignore'))
                success = True
            else:
                print("❌ Keine Antwort")
                success = False

        except socket.timeout:
            print(f"Fehler: timed out")
            success = False
        except Exception as e:
            print(f"Fehler: {e}")
            success = False
        finally:
            if sock:
                sock.close()
    else:
        # Hex command mode
        print("Modus: Hex-Befehle")
        success = query_configuration(args.ip, args.port, args.timeout, args.command)

    print("\n" + "=" * 60)
    if success:
        print("✅ Abfrage erfolgreich")
        sys.exit(0)
    else:
        print("❌ Abfrage fehlgeschlagen")
        sys.exit(1)

if __name__ == "__main__":
    main()
