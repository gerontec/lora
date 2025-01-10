#!/usr/bin/env python3
import serial
import logging
import time
import subprocess

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
    gateway = get_default_gateway()
    gateway_message = f"Gateway: {gateway}".encode('utf-8')
    ser.write(gateway_message + b'\r\n')
    ser.write(rssi_command)
    logging.info(f"Sent RSSI query command: {rssi_command.hex().upper()}")

def process_rssi_response(response):
    if len(response) < 4 or not response.startswith(b'\xC1'):
        return None
    # Expected format: C1 + address + read length + RSSI value
    rssi_value = response[3]
    return {
        "RSSI Value": - (256 - rssi_value)
    }

def send_ack(ser):
    ack_message = b"ACK\r\n"
    ser.write(ack_message)
    logging.info(f"Sent ACK response")

def main():
    ser = setup_serial()
    if ser is None:
        logging.info("Failed to open serial port. Exiting.")
        return

    logging.info("Listening for incoming LoRa messages...")

    # Enable RSSI once at the start
    ser.write(b"Channel RSSI enabled\r\n")
    logging.info("Sent RSSI enable command: Channel RSSI enabled")

    # Use a buffer for accumulating message data
    message_buffer = bytearray()

    try:
        i = 0
        while True:  # Changed from range to an infinite loop to keep the script running
            # Read any incoming data which might include UTF-8 messages or RSSI responses
            normal_data = ser.read(240)  # Increased buffer size
            
            if normal_data:
                message_buffer.extend(normal_data)
                
                # Process all data in the buffer
                while message_buffer:
                    # Try to find an RSSI response first
                    if b'\xC1' in message_buffer:
                        start = message_buffer.find(b'\xC1')
                        if start + 4 <= len(message_buffer):  # Ensure we have at least 4 bytes for RSSI response
                            rssi_response = message_buffer[start:start+4]  # Assuming RSSI response is 4 bytes long
                            rssi_values = process_rssi_response(rssi_response)
                            if rssi_values:
                                logging.info(f"RSSI Value: {rssi_values['RSSI Value']} dBm from Gateway {get_default_gateway()}")
                            del message_buffer[start:start+4]
                        else:
                            break  # Wait for more data if we don't have enough for an RSSI response
                    else:
                        # If no RSSI response, try to decode as UTF-8 message
                        try:
                            end_of_message = message_buffer.find(b'\n')
                            if end_of_message != -1:
                                decoded_msg = message_buffer[:end_of_message+1].decode('utf-8', errors='ignore').strip()
                                # Add default gateway to the log message
                                logging.info(f"Received UTF-8 message from Gateway {get_default_gateway()}: {decoded_msg}")
                                # Send ACK for each received message
                                send_ack(ser)
                                del message_buffer[:end_of_message+1]
                            else:
                                # If no newline is found, this might be part of a larger message, so wait for more data
                                break
                        except UnicodeDecodeError:
                            # If decoding fails, log the raw data in hex and clear buffer
                            logging.info(f"Received non-UTF-8 data (hex) from Gateway {get_default_gateway()}: {message_buffer.hex(' ').upper()}")
                            message_buffer.clear()

            # Send RSSI command once per minute
            if i % 60 == 0:  # 60 iterations at 1 second each equals 1 minute
                send_rssi_command(ser)
            
            i += 1
            time.sleep(1)  # Sleep for 1 second to keep the loop running but not too fast

    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        ser.close()

if __name__ == "__main__":
    main()
