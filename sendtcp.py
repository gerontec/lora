#!/usr/bin/python3
import socket
import time
import logging
import threading

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

def send_message(sock, message):
    sock.send(message.encode() + b'\r\n')  # Append CRLF for proper termination
    #logging.info(f"Sent: {message}")  # Log sent message

def receive_messages(sock):
    while True:
        incoming = sock.recv(BUFFER_SIZE)
        if incoming:
            decoded_message = incoming.decode(errors='ignore')
            print(f"Received: {decoded_message}")
            logging.info(f"Received: {decoded_message}")  # Log received message

logging.info(f"Sent: ")  # Log sent message
# Create a TCP socket
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((TCP_IP, TCP_PORT))
    
    # Start receiving messages in a separate thread
    receiver_thread = threading.Thread(target=receive_messages, args=(s,), daemon=True)
    receiver_thread.start()

    # Send messages every 5 seconds
    while True:
        message = "HELLO world was sent to 192.168.4.101:8886"
        send_message(s, message)
        time.sleep(5)  # Wait for 5 seconds before sending the next message
