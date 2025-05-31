import socket
import struct
import threading
from pathlib import Path
from queue import Empty, Queue
from time import sleep
from typing import Final

# Constants for retry behavior and connection timeout
MAX_RETRIES: Final[int] = 3
CONNECT_TIMEOUT_IN_SECONDS: Final[int] = 5

# Peer2Peer manages a bidirectional connection using two sockets:
# one for sending and one for receiving data, enabling peer-to-peer communication.
class Peer2Peer:
    peer_ip: str
    send_port: int
    receive_port: int

    sender_socket: socket.socket
    receiver_socket: socket.socket
    connection_socket: socket.socket

    received_messages_queue: Queue

    # Initializes the sender and receiver sockets and starts threads to connect them
    def __init__(self, peer_ip, send_port, receive_port):
        self.peer_ip = peer_ip
        self.send_port = send_port
        self.receive_port = receive_port

        # Socket for sending messages to the peer
        self.sender_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Socket for listening for incoming connections
        self.receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Bind the receiver socket to the specified port and start listening
        self.receiver_socket.bind(('0.0.0.0', self.receive_port))
        self.receiver_socket.listen(1)

        self.running = True  # Flag for the receive loop

        # Start threads to establish connections in parallel
        receiver_connect_thread = threading.Thread(target=self.connect_receiver_to_peer)
        sender_connect_thread = threading.Thread(target=self.connect_sender_to_peer)

        receiver_connect_thread.start()
        sender_connect_thread.start()

        # Wait until both threads finish before continuing
        receiver_connect_thread.join()
        sender_connect_thread.join()

        # Queue to store received messages
        self.received_messages_queue = Queue()

        # Start the background thread to continuously receive data
        self.receiver_thread = threading.Thread(target=self.receive_data, daemon=True)
        self.receiver_thread.start()

    # Accept an incoming connection on the receiver socket
    def connect_receiver_to_peer(self):
        self.connection_socket, _ = self.receiver_socket.accept()

    # Attempt to connect the sender socket to the peer's listening port
    def connect_sender_to_peer(self):
        retries = 0
        while True:
            try:
                self.sender_socket.connect((self.peer_ip, self.send_port))
                print(f"Connected to peer at {self.peer_ip}:{self.send_port}")
                break
            except:
                retries += 1
                if retries >= MAX_RETRIES:
                    raise  # Too many failures, give up
                sleep(CONNECT_TIMEOUT_IN_SECONDS)  # Wait before retrying

    # Send a message to the peer with a 4-byte length prefix
    def send_message(self, data: bytes):
        length_prefix = struct.pack("!I", len(data))  # 4-byte prefix in big-endian format
        self.sender_socket.sendall(length_prefix + data)

    # Continuously listens for incoming data and pushes it into the message queue
    def receive_data(self):
        print(f"Listening for incoming connections on port {self.receive_port}...")
        while self.running:
            try:
                # Receive 4 bytes indicating the message length
                length_prefix = self._recv_exactly(4)
                if not length_prefix:
                    break

                # Get message length and receive the message
                message_length = struct.unpack("!I", length_prefix)[0]
                message_data = self._recv_exactly(message_length)
                if not message_data:
                    break

                # Put the complete message into the queue
                self.received_messages_queue.put(message_data)

            except Exception as e:
                print(f"Error receiving message: {e}")
        self.close()

    # Helper method to ensure exactly 'size' bytes are received from the connection
    def _recv_exactly(self, size: int) -> bytes:
        data = b""
        while len(data) < size:
            chunk_size = min(1024, size - len(data))  # Read in chunks
            packet = self.connection_socket.recv(chunk_size)
            if not packet:
                return b""  # Connection closed
            data += packet
        return data

    # Retrieves a message from the queue, blocking until one is available
    def get_message(self) -> bytes:
        while self.running:
            try:
                return self.received_messages_queue.get(timeout=1)
            except Empty:
                continue  # Retry until message is received or connection closes

        raise Exception("Connection closed")

    # Gracefully shuts down all sockets and terminates the receive thread
    def close(self):
        self.running = False
        self.sender_socket.close()
        self.receiver_socket.close()
        print("Connections closed.")

    # Sends a file as binary data over the connection
    def send_file(self, file_path: str | Path):
        with open(file_path, "rb") as file:
            file_data = file.read()

        self.send_message(file_data)

    # Receives a file from the peer and writes it to the given output path
    def get_file(self, output_path: str | Path):
        file_data = self.get_message()

        with open(output_path, "wb") as file:
            file.write(file_data)
