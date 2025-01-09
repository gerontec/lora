#!/usr/bin/python3
import socket
import argparse

TCP_IP = '192.168.4.101'
TCP_PORT = 8886
BUFFER_SIZE = 1024

def main():
    parser = argparse.ArgumentParser(description="Configure E90-DTU(xxxSLxx-ETH) via TCP.")
    parser.add_argument('--addr', type=int, default=None, help='Local address (0-65535)')
    parser.add_argument('--netid', type=int, default=None, help='Network ID (0-255)')
    parser.add_argument('--air-baud', choices=['300', '600', '1200', '2400', '4800', '9600', '19200', '38400', '62500'], default=None, help='Air data rate')
    parser.add_argument('--pack-length', choices=['240', '128', '64', '32'], default=None, help='Packet length')
    parser.add_argument('--rssi-en', choices=['RSCHOFF', 'RSCHON'], default=None, help='Ambient Noise Enable')
    parser.add_argument('--tx-pow', choices=['PWMAX', 'PWMID', 'PWLOW', 'PWMIN'], default=None, help='Transmit power')
    parser.add_argument('--ch', type=int, default=None, help='Channel number (0-83 for 400SL)')
    parser.add_argument('--rssi-data', choices=['RSDATOFF', 'RSDATON'], default=None, help='Data Noise Enable')
    parser.add_argument('--tr-mod', choices=['TRNOR', 'TRFIX'], default=None, help='Transfer method')
    parser.add_argument('--relay', choices=['RLYOFF', 'RLYON'], default=None, help='Relay function')
    parser.add_argument('--lbt', choices=['LBTOFF', 'LBTON'], default=None, help='LBT Enable')
    parser.add_argument('--wor', choices=['WORRX', 'WORTX', 'WOROFF'], default=None, help='WOR Mode')
    parser.add_argument('--wor-tim', choices=['500', '1000', '1500', '2000', '2500', '3000', '3500', '4000'], default=None, help='WOR period (ms)')
    parser.add_argument('--crypt', type=int, default=None, help='Communication key (0-65535)')
    args = parser.parse_args()

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((TCP_IP, TCP_PORT))
            print(f"Connected to {TCP_IP}:{TCP_PORT}")

            if any(v is not None for v in vars(args).values()):
                # Construct the command to set LoRa parameters
                params = []
                for key, value in vars(args).items():
                    if value is not None:
                        params.append(str(value))
                
                # If some parameters are provided, construct the set command
                set_command = f"AT+LORA={','.join(params)}\r\n"
                s.send(set_command.encode())
                response = s.recv(BUFFER_SIZE).decode().strip()
                print(f"Setting LoRa parameters: {response}")
            else:
                # No arguments provided, query current configuration and show possible commands
                s.send(b"AT+LORA\r\n")
                response = s.recv(BUFFER_SIZE).decode().strip()
                print(f"Current LoRa Configuration: {response}")
                
                print("\nPossible Commands:")
                for action in parser._actions[1:]:  # Skip the first action which is help
                    print(f"--{action.dest}: {action.help}")

    except ConnectionRefusedError:
        print(f"Connection to {TCP_IP}:{TCP_PORT} refused. Make sure the server is running.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
