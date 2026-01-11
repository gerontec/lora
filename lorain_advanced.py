#!/usr/bin/env python3
"""
Advanced LoRa Monitor with Message Deduplication
- Adds unique message IDs to prevent backhaul loops
- Filters own messages returned via repeater
- Supports both simple monitoring and two-way communication
"""
import serial
import logging
import time
import subprocess
import hashlib
from collections import deque

# Configure logging to file only
logging.basicConfig(filename='/tmp/lorain.log', level=logging.INFO,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# Generate unique node ID (based on hostname or MAC)
def get_node_id():
    try:
        result = subprocess.run(['hostname'], capture_output=True, text=True, check=True)
        hostname = result.stdout.strip()
        # Create short hash of hostname
        node_hash = hashlib.md5(hostname.encode()).hexdigest()[:6]
        return f"NODE_{node_hash.upper()}"
    except:
        return "NODE_UNKNOWN"

NODE_ID = get_node_id()

def get_default_gateway():
    try:
        # Use ip route command to fetch the default gateway
        result = subprocess.run(['ip', 'route', 'show', 'default'], capture_output=True, text=True, check=True)
        gateway_line = result.stdout.split('\n')[0]
        gateway = gateway_line.split()[2]
        return gateway
    except subprocess.CalledProcessError:
        logging.error("Failed to retrieve default gateway")
        return "Unknown"

def setup_serial():
    try:
        ser = serial.Serial(
            port='/dev/ttyUSB0',
            baudrate=9600,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=1  # Timeout in seconds for reading
        )
        return ser
    except serial.SerialException as e:
        logging.error(f"Error opening serial port: {e}")
        return None

def send_rssi_command(ser):
    # Command to read RSSI as byte sequence
    rssi_command = b'\xC0\xC1\xC2\xC3\x00\x02'  # Command to read registers 0x00 and 0x01
    ser.write(rssi_command)
    logging.info(f"Sent RSSI query command: {rssi_command.hex().upper()}")

def process_rssi_response(response):
    if not response.startswith(b'\xC1'):
        return None
    # Expected format: C1 + address + read length + RSSI value
    rssi_value = response[3]
    return {
        "RSSI Value": - (256 - rssi_value)
    }

def send_message_with_id(ser, message, msg_id, sent_messages):
    """
    Send message with unique ID to prevent backhaul confusion
    Format: [NODE_ID:MSG_ID] message content
    """
    formatted_msg = f"[{NODE_ID}:{msg_id}] {message}\r\n"
    ser.write(formatted_msg.encode('utf-8'))
    sent_messages.append(formatted_msg.strip())
    logging.info(f"Sent message: {formatted_msg.strip()}")
    return formatted_msg

def parse_message(msg):
    """
    Parse message format: [NODE_ID:MSG_ID] content
    Returns: (node_id, msg_id, content) or (None, None, msg) if not formatted
    """
    if msg.startswith('[') and ']' in msg:
        try:
            header_end = msg.index(']')
            header = msg[1:header_end]
            content = msg[header_end+1:].strip()
            if ':' in header:
                node_id, msg_id = header.split(':', 1)
                return (node_id, msg_id, content)
        except:
            pass
    return (None, None, msg)

def main():
    ser = setup_serial()
    if ser is None:
        logging.info("Failed to open serial port. Exiting.")
        return

    logging.info(f"Starting LoRa Monitor - Node ID: {NODE_ID}")
    logging.info("Listening for incoming LoRa messages...")

    # Track recently sent messages to filter out backhaul (own messages returning via repeater)
    sent_messages = deque(maxlen=20)  # Keep last 20 sent messages
    message_counter = 0

    # Use a buffer for accumulating message data
    message_buffer = bytearray()

    try:
        i = 0
        while True:
            # Read any incoming data which might include UTF-8 messages or RSSI responses
            normal_data = ser.read(240)

            if normal_data:
                message_buffer.extend(normal_data)

                while message_buffer:
                    if b'\xC1' in message_buffer:
                        start = message_buffer.find(b'\xC1')
                        if start + 4 <= len(message_buffer):
                            rssi_response = message_buffer[start:start+4]
                            rssi_values = process_rssi_response(rssi_response)
                            if rssi_values:
                                rssi_val = rssi_values['RSSI Value']
                                logging.info(f"RSSI Value: {rssi_val} dBm")

                                # Send RSSI with message ID to prevent backhaul loop
                                message_counter += 1
                                send_message_with_id(ser, f"RSSI:{rssi_val}dBm", message_counter, sent_messages)

                            del message_buffer[start:start+4]
                        else:
                            break
                    else:
                        try:
                            end_of_message = message_buffer.find(b'\n')
                            if end_of_message != -1:
                                decoded_msg = message_buffer[:end_of_message+1].decode('utf-8', errors='ignore').strip()

                                # Parse message to extract node ID
                                node_id, msg_id, content = parse_message(decoded_msg)

                                # Filter out own messages (backhaul from repeater)
                                if node_id == NODE_ID:
                                    logging.info(f"[BACKHAUL-FILTERED] Own message via repeater: {decoded_msg}")
                                elif decoded_msg in sent_messages:
                                    logging.info(f"[DUPLICATE-FILTERED] Already sent: {decoded_msg}")
                                else:
                                    if node_id:
                                        logging.info(f"Received from {node_id} (msg {msg_id}): {content}")
                                    else:
                                        logging.info(f"Received: {decoded_msg}")

                                del message_buffer[:end_of_message+1]
                            else:
                                break
                        except UnicodeDecodeError:
                            logging.info(f"Received non-UTF-8 data (hex): {message_buffer.hex(' ').upper()}")
                            message_buffer.clear()

            # Send RSSI command every 10 seconds
            if i % 10 == 0:
                send_rssi_command(ser)

            i += 1
            time.sleep(1)

    except KeyboardInterrupt:
        logging.info("Shutting down gracefully...")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        ser.close()

if __name__ == "__main__":
    main()
