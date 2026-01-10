#!/usr/bin/python3
import socket
import time
import logging
import threading
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    filename='/tmp/e90-dtu.log',  # Log file name
    level=logging.INFO,                 # Log level
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log format
)

# Configure the TCP connection
TCP_IP = '192.168.4.101'  # Change this to your device's IP
TCP_PORT = 8886
BUFFER_SIZE = 240
SOCKET_TIMEOUT = 10  # seconds - timeout for connection and recv operations

def send_message(sock, message):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"{current_time} - {message}"
    sock.send(full_message.encode() + b'\r\n')  # Append CRLF for proper termination
    logging.info(f"Sent: {full_message}")  # Log sent message with timestamp

def send_rssi_command(sock):
    # Send command to read RSSI
    #rssi_command = b"C0C1C2C30001"  # Command to read registers 0x00 and 0x01
    rssi_command = b'\xC0\xC1\xC2\xC3\x00\x02'
    sock.send(rssi_command)
    logging.info(f"Sent: {rssi_command.hex().upper()}")  # Log in hex for clarity

def receive_messages(sock):
    while True:
        try:
            incoming = sock.recv(BUFFER_SIZE)
            if incoming:
                # Try to interpret incoming data as RSSI response
                if incoming.startswith(b'\xC1') and len(incoming) >= 4:
                    # Assuming RSSI is the 4th byte (index 3)
                    rssi_value = incoming[3]
                    rssi_dbm = - (256 - rssi_value)
                    logging.info(f"Received RSSI: {rssi_dbm} dBm")
                else:
                    # If it's not an RSSI response, treat it as a regular message
                    decoded_message = incoming.decode(errors='ignore').strip()
                    print(f"Received: {decoded_message}")
                    logging.info(f"Received: {decoded_message}")
        except Exception as e:
            logging.error(f"Error receiving message: {e}")
            break  # Exit the loop if there's an error (like connection lost)

# Create a TCP socket
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    # Set timeout to prevent indefinite blocking
    s.settimeout(SOCKET_TIMEOUT)

    try:
        s.connect((TCP_IP, TCP_PORT))
        logging.info(f"Connected to {TCP_IP}:{TCP_PORT}")
    except socket.timeout:
        logging.error(f"Connection timeout after {SOCKET_TIMEOUT}s")
        print(f"Error: Cannot connect to {TCP_IP}:{TCP_PORT} - timeout")
        sys.exit(1)
    except ConnectionRefusedError:
        logging.error(f"Connection refused to {TCP_IP}:{TCP_PORT}")
        print(f"Error: Connection refused by {TCP_IP}:{TCP_PORT}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Connection error: {e}")
        print(f"Error: {e}")
        sys.exit(1)
    
    # Start receiving messages in a separate thread
    receiver_thread = threading.Thread(target=receive_messages, args=(s,), daemon=True)
    receiver_thread.start()

    # Enable RSSI once at the start, in case it wasn't previously enabled
    send_rssi_command(s)

    # Main loop to send messages and RSSI commands
    try:
        while True:
            message = "HELLO world was sent to 192.168.4.101:8886"
            send_message(s, message)
            
            # Send RSSI command every cycle
            send_rssi_command(s)
            
            time.sleep(5)  # Wait for 5 seconds before sending the next message and RSSI command
    except KeyboardInterrupt:
        logging.info("Interrupted by user. Stopping...")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
