import socket
import threading
import struct
from pathlib import Path
from queue import Queue, Empty
from time import sleep
from typing import Final

MAX_RETRIES: Final[int] = 3
CONNECT_TIMEOUT_IN_SECONDS: Final[int] = 5


class Peer2Peer:
    peer_ip: str
    send_port: int
    receive_port: int

    sender_socket: socket.socket
    receiver_socket: socket.socket
    connection_socket: socket.socket

    received_messages_queue: Queue

    def __init__(self, peer_ip, send_port, receive_port):
        self.peer_ip = peer_ip
        self.send_port = send_port
        self.receive_port = receive_port

        self.sender_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.receiver_socket.bind(('0.0.0.0', self.receive_port))
        self.receiver_socket.listen(1)

        self.running = True

        receiver_connect_thread = threading.Thread(target=self.connect_receiver_to_peer)
        sender_connect_thread = threading.Thread(target=self.connect_sender_to_peer)

        receiver_connect_thread.start()
        sender_connect_thread.start()

        receiver_connect_thread.join()
        sender_connect_thread.join()

        self.received_messages_queue = Queue()

        self.receiver_thread = threading.Thread(target=self.receive_data, daemon=True)
        self.receiver_thread.start()

    def connect_receiver_to_peer(self):
        self.connection_socket, _ = self.receiver_socket.accept()

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
                    raise
                sleep(CONNECT_TIMEOUT_IN_SECONDS)

    def send_message(self, data: bytes):
        length_prefix = struct.pack("!I", len(data))  # 4-byte prefix (big-endian)
        self.sender_socket.sendall(length_prefix + data)

    def receive_data(self):
        print(f"Listening for incoming connections on port {self.receive_port}...")
        while self.running:
            try:
                length_prefix = self._recv_exactly(4)
                if not length_prefix:
                    break

                message_length = struct.unpack("!I", length_prefix)[0]
                message_data = self._recv_exactly(message_length)
                if not message_data:
                    break
                self.received_messages_queue.put(message_data)

            except Exception as e:
                print(f"Error receiving message: {e}")
        self.close()

    def _recv_exactly(self, size: int) -> bytes:
        """Helper function to receive exactly 'size' bytes."""
        data = b""
        while len(data) < size:
            chunk_size = min(1024, size - len(data))
            packet = self.connection_socket.recv(chunk_size)
            if not packet:
                return b""  # Connection closed
            data += packet
        return data

    def get_message(self) -> bytes:
        while self.running:
            try:
                return self.received_messages_queue.get(timeout=1)
            except Empty:
                continue

        raise Exception("Connection closed")


    def close(self):
        """Close all sockets and stop the listener."""
        self.running = False
        self.sender_socket.close()
        self.receiver_socket.close()
        print("Connections closed.")

    def send_file(self, file_path: str | Path):
        with open(file_path, "rb") as file:
            file_data = file.read()

        self.send_message(file_data)

    def get_file(self, output_path: str | Path):
        file_data = self.get_message()

        with open(output_path, "wb") as file:
            file.write(file_data)
