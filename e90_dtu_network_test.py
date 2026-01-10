#!/usr/bin/python3
"""
E90-DTU Network Diagnostic Tool
Tests network connectivity and helps find the correct IP and port

Usage:
    python3 e90_dtu_network_test.py --ip 192.168.4.101
    python3 e90_dtu_network_test.py --scan-subnet 192.168.4.0/24
"""

import socket
import subprocess
import argparse
import ipaddress
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

class E90DTUNetworkTester:
    def __init__(self, timeout=2):
        self.timeout = timeout

    def ping_host(self, ip):
        """Ping a host to check if it's reachable"""
        try:
            # Use platform-appropriate ping command
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '1', str(ip)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=self.timeout
            )
            return result.returncode == 0
        except:
            return False

    def test_port(self, ip, port):
        """Test if a specific port is open on a host"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((str(ip), port))
            sock.close()
            return result == 0
        except:
            return False

    def test_at_command(self, ip, port):
        """Try to send AT command and check response"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((str(ip), port))

            # Send AT command
            sock.sendall(b"AT\r\n")
            time.sleep(0.5)

            # Try to receive response
            sock.settimeout(0.5)
            try:
                response = sock.recv(1024)
                sock.close()

                if response:
                    decoded = response.decode('ascii', errors='ignore').strip()
                    return True, decoded
            except socket.timeout:
                pass

            sock.close()
            return False, None

        except:
            return False, None

    def scan_single_host(self, ip, ports):
        """Scan a single host for open ports"""
        print(f"\n🔍 Testing {ip}...")

        # First check if host is reachable
        if not self.ping_host(ip):
            print(f"   ✗ Host unreachable (no ping response)")
            return None

        print(f"   ✓ Host is reachable")

        # Test each port
        open_ports = []
        for port in ports:
            if self.test_port(ip, port):
                print(f"   ✓ Port {port} is OPEN", end='')

                # Try AT command
                at_works, response = self.test_at_command(ip, port)
                if at_works:
                    print(f" - AT command works! Response: {response}")
                    open_ports.append((port, True, response))
                else:
                    print(f" - No AT response (may be data port)")
                    open_ports.append((port, False, None))
            else:
                print(f"   ✗ Port {port} is closed")

        return open_ports if open_ports else None

    def scan_subnet(self, subnet, ports):
        """Scan entire subnet for E90-DTU devices"""
        print(f"\n{'='*60}")
        print(f"Scanning subnet: {subnet}")
        print(f"Testing ports: {ports}")
        print(f"{'='*60}")

        network = ipaddress.ip_network(subnet, strict=False)
        found_devices = []

        # Scan hosts in parallel
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = {}
            for ip in network.hosts():
                future = executor.submit(self.scan_single_host, str(ip), ports)
                futures[future] = str(ip)

            for future in as_completed(futures):
                ip = futures[future]
                try:
                    result = future.result()
                    if result:
                        found_devices.append((ip, result))
                except Exception as e:
                    print(f"   Error scanning {ip}: {e}")

        return found_devices

    def display_summary(self, found_devices):
        """Display summary of found devices"""
        print(f"\n{'='*60}")
        print("SCAN SUMMARY")
        print(f"{'='*60}")

        if not found_devices:
            print("\n✗ No E90-DTU devices found")
            print("\nTroubleshooting:")
            print("  1. Check device is powered on")
            print("  2. Verify network cable is connected")
            print("  3. Check you're on the correct subnet")
            print("  4. Try direct connection (computer <-> DTU)")
            print("  5. Reset device to factory defaults")
            return

        print(f"\n✓ Found {len(found_devices)} device(s):\n")

        for ip, ports in found_devices:
            print(f"📍 {ip}")
            for port, at_works, response in ports:
                if at_works:
                    print(f"   ✓ Port {port} - Configuration port (AT commands work)")
                    print(f"     Response: {response}")
                    print(f"     Command: python3 e90_dtu_config_reader_network.py --ip {ip} --port {port}")
                else:
                    print(f"   • Port {port} - Open (possibly data port)")
            print()

    def test_single_device(self, ip, ports):
        """Test a single device"""
        print(f"\n{'='*60}")
        print(f"E90-DTU Network Diagnostic Test")
        print(f"{'='*60}")

        result = self.scan_single_host(ip, ports)

        print(f"\n{'='*60}")
        print("TEST RESULTS")
        print(f"{'='*60}")

        if not result:
            print(f"\n✗ No accessible ports found on {ip}")
            print("\nTroubleshooting:")
            print(f"  1. Verify IP address: ping {ip}")
            print(f"  2. Check firewall settings")
            print(f"  3. Try different ports: --ports 8080,8886,8899,23")
            print(f"  4. Access web interface: http://{ip}")
            print(f"  5. Check device manual for correct port")
        else:
            print(f"\n✓ Device accessible at {ip}")
            print(f"\nOpen ports:")

            config_port = None
            for port, at_works, response in result:
                if at_works:
                    print(f"  ✓ Port {port} - Configuration port")
                    print(f"    AT Response: {response}")
                    config_port = port
                else:
                    print(f"  • Port {port} - Open")

            if config_port:
                print(f"\n💡 To read configuration, run:")
                print(f"   python3 e90_dtu_config_reader_network.py --ip {ip} --port {config_port}")
            else:
                print(f"\n⚠  No configuration port found (no AT response)")
                print(f"   Try accessing web interface: http://{ip}")

        print()


def main():
    parser = argparse.ArgumentParser(
        description='E90-DTU Network Diagnostic Tool',
        epilog='Tests network connectivity and finds E90-DTU devices'
    )

    parser.add_argument(
        '--ip', '-i',
        help='Test specific IP address'
    )

    parser.add_argument(
        '--scan-subnet', '-s',
        help='Scan entire subnet (e.g., 192.168.4.0/24)'
    )

    parser.add_argument(
        '--ports', '-p',
        default='8886,8080,8899,23,80',
        help='Comma-separated list of ports to test (default: 8886,8080,8899,23,80)'
    )

    parser.add_argument(
        '--timeout', '-t',
        type=float,
        default=2.0,
        help='Timeout for each test in seconds (default: 2.0)'
    )

    args = parser.parse_args()

    # Parse ports
    try:
        ports = [int(p.strip()) for p in args.ports.split(',')]
    except:
        print("✗ Invalid port format. Use comma-separated numbers (e.g., 8886,8080,23)")
        sys.exit(1)

    # Create tester
    tester = E90DTUNetworkTester(timeout=args.timeout)

    # Run appropriate test
    if args.scan_subnet:
        # Subnet scan
        try:
            found = tester.scan_subnet(args.scan_subnet, ports)
            tester.display_summary(found)
        except ValueError as e:
            print(f"✗ Invalid subnet format: {e}")
            print("  Example: --scan-subnet 192.168.4.0/24")
            sys.exit(1)

    elif args.ip:
        # Single host test
        tester.test_single_device(args.ip, ports)

    else:
        # No arguments - show help
        parser.print_help()
        print("\n" + "="*60)
        print("Examples:")
        print("="*60)
        print("\n# Test specific IP with default ports")
        print("python3 e90_dtu_network_test.py --ip 192.168.4.101")
        print("\n# Test specific IP with custom ports")
        print("python3 e90_dtu_network_test.py --ip 192.168.4.101 --ports 8886,9000,10000")
        print("\n# Scan entire subnet")
        print("python3 e90_dtu_network_test.py --scan-subnet 192.168.4.0/24")
        print("\n# Quick scan with fast timeout")
        print("python3 e90_dtu_network_test.py --scan-subnet 192.168.1.0/24 --timeout 1.0")
        print()


if __name__ == "__main__":
    main()
