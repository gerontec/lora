#!/usr/bin/env python3
import serial
import logging
import time

# Configure logging
logging.basicConfig(filename='/tmp/lorain.log', level=logging.INFO, 
                    format='%(asctime)s - %(message)s', 
                    datefmt='%Y-%m-%d %H:%M:%S')

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

def decode_partial_utf8(data):
    try:
        return data.decode('utf-8'), b''
    except UnicodeDecodeError as e:
        # Decode up to the point of the error
        valid_part = data[:e.start].decode('utf-8')
        invalid_bytes = data[e.start:]
        return valid_part, invalid_bytes

def main():
    ser = setup_serial()
    if ser is None:
        print("Failed to open serial port. Exiting.")
        return

    print("Listening for incoming LoRa messages...")

    try:
        while True:
            # Read from the serial port
            data = ser.read(100)  # Adjust the buffer size according to your needs
            if data:
                decoded, remaining = decode_partial_utf8(data)
                if remaining:
                    # Log both the decoded part and the remaining hex part
                    log_message = f"Received: {decoded} (hex: {remaining.hex(' ').upper()})"
                else:
                    log_message = f"Received: {decoded}"
                
                logging.info(log_message)
                print(log_message)  # Optional: Print to console
    except KeyboardInterrupt:
        print("Interrupted by user. Stopping...")
    finally:
        ser.close()

if __name__ == "__main__":
    main()
