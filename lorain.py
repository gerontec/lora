#!/usr/bin/env python3
import serial
import logging
import time
import socket

# Configure logging to file only
logging.basicConfig(filename='/tmp/lorain.log', level=logging.INFO, 
                    format='%(asctime)s - %(message)s', 
                    datefmt='%Y-%m-%d %H:%M:%S')

def get_local_ip_address():
    try:
        # Get the hostname
        hostname = socket.gethostname()
        # Get the IP address associated with that hostname
        ip_address = socket.gethostbyname(hostname)
        return ip_address
    except socket.error:
        logging.error("Failed to get local IP address")
        return "0.0.0.0"  # Return a default value if fetching the IP fails

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
    rssi_command = b'\xC0\xC1\xC2\xC3\x00\x01'  # Command to read registers 0x00 and 0x01
    
    # Get the local IP address
    ip_address = get_local_ip_address()
    ip_message = f"lorain.py {ip_address}".encode('utf-8')
    ser.write(ip_message)
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

def main():
    ser = setup_serial()
    if ser is None:
        logging.info("Failed to open serial port. Exiting.")
        return

    logging.info("Listening for incoming LoRa messages...")

    # Enable RSSI once at the start
    ser.write(b"Channel RSSI enabled\r\n")
    logging.info("Sent RSSI enable command: Channel RSSI enabled")

    try:
        for i in range(100):  # Example: perform 100 RSSI queries
            # Read any incoming data that might be UTF-8 messages
            normal_data = ser.read(200)  # Read buffer for potential UTF-8 messages
            if normal_data:
                try:
                    # Attempt to decode as UTF-8
                    decoded_msg = normal_data.decode('utf-8', errors='ignore')
                    if decoded_msg.strip():  # Avoid logging empty strings
                        logging.info(f"Received UTF-8 message: {decoded_msg.strip()}")
                except UnicodeDecodeError:
                    # If not UTF-8, log in hex
                    logging.info(f"Received non-UTF-8 data (hex): {normal_data.hex(' ').upper()}")

            send_rssi_command(ser)
            
            # Read specifically for RSSI response
            time.sleep(0.1)  # Small delay to give the module time to respond
            rssi_response = ser.read(20)  # Read more to capture potentially multiple responses
            
            # Split the response into individual responses if multiple are received
            responses = rssi_response.split(b'\xC1')
            for resp in responses:
                if resp and len(resp) >= 3:  # Ensure there's enough data to process
                    full_response = b'\xC1' + resp
                    rssi_values = process_rssi_response(full_response)
                    if rssi_values:
                        logging.info(f"RSSI Value: {rssi_values['RSSI Value']} dBm")
                    else:
                        logging.info(f"Possible RSSI response (hex): {full_response.hex(' ').upper()} - Unrecognized format")

    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        ser.close()

if __name__ == "__main__":
    main()
