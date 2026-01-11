#!/usr/bin/env python3
import serial
import logging
import time
import subprocess
from collections import deque

# Configure logging to file only
logging.basicConfig(filename='/tmp/lorain.log', level=logging.INFO,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

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

def main():
    ser = setup_serial()
    if ser is None:
        logging.info("Failed to open serial port. Exiting.")
        return

    logging.info("Listening for incoming LoRa messages...")

    # Track recently sent messages to filter out backhaul (own messages returning via repeater)
    sent_messages = deque(maxlen=10)  # Keep last 10 sent messages

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
                                logging.info(f"RSSI Value: {rssi_val} dBm from {get_default_gateway()}")

                                # ✅ FIX: Don't send RSSI back to prevent backhaul loop!
                                # Instead, just log it locally
                                # Original code: send_rssi_back(ser, rssi_val)

                            del message_buffer[start:start+4]
                        else:
                            break
                    else:
                        try:
                            end_of_message = message_buffer.find(b'\n')
                            if end_of_message != -1:
                                decoded_msg = message_buffer[:end_of_message+1].decode('utf-8', errors='ignore').strip()

                                # ✅ FIX: Filter out own messages (backhaul from repeater)
                                if decoded_msg not in sent_messages:
                                    logging.info(f"Received UTF-8 from {get_default_gateway()}: {decoded_msg}")
                                else:
                                    logging.info(f"[FILTERED] Own message returned via repeater: {decoded_msg}")

                                del message_buffer[:end_of_message+1]
                            else:
                                break
                        except UnicodeDecodeError:
                            logging.info(f"Received non-UTF-8 data (hex) from Gateway {get_default_gateway()}: {message_buffer.hex(' ').upper()}")
                            message_buffer.clear()

            # Send RSSI command every 10 seconds (i % 10 == 0)
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
