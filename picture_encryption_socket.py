import os
import shutil
from queue import Empty, Queue
from threading import Event, Thread
from typing import Final

from PIL import Image

from aes_cipher import AESCipher
from data_info import SplittedImageInfo
from dh_key_exchange import DH_Endpoint
from image_metadata import add_metadata_to_image, read_metadata_from_image
from image_split import restore_image, split_image
from p2p import Peer2Peer
from random_image import generate_random_image
from steganography import hide_message_in_image, reveal_message_from_image
from utils import (bytes_to_int, create_random_name_directory, find_primitive_root, generate_random_filename,
                   get_temp_dir, int_to_bytes, random_prime_number, row_and_column_to_str,
                   str_to_row_and_column, generate_5_digit_number)
from zip_files import create_zip_file, extract_zip_file

MAX_CONTENT_LENGTH: Final[int] = 115167  # Maximum allowed size for the content being sent


class PictureEncryptionSocket:
    """
    PictureEncryptionSocket handles encrypted communication between peers by
    embedding encrypted messages inside images using steganography.
    It splits the image into parts, sends them over the network, and reconstructs
    and decrypts the message on the receiver side.

    The connection uses Diffie-Hellman key exchange to agree on a shared secret
    encryption key, which is then used for AES encryption of the message.
    """

    def __init__(self, peer_ip: str) -> None:
        """
        Initialize the socket with the target peer's IP address.
        Sets up threading events and queues for sending and receiving data.
        """
        self.stop_event = Event()
        self.peer_ip = peer_ip
        self.send_queue = Queue()  # Queue for outgoing data to send
        self.recv_queue = Queue()  # Queue for incoming received data
        self.sender_thread = Thread()
        self.receiver_thread = Thread()
        self.is_connected = True  # Mark connection status as connected immediately
        self.peer_send = None
        self.peer_receive = None

    def connect(self) -> None:
        """
        Starts sender and receiver threads to handle communication asynchronously.
        """
        self.sender_thread = Thread(target=self.__safe_send_loop)
        self.receiver_thread = Thread(target=self.__safe_receive_loop)

        self.sender_thread.start()
        self.receiver_thread.start()

        self.is_connected = True

    def send(self, data: bytes) -> None:
        """
        Adds data to the send queue to be processed by the sender thread.
        Raises an exception if the socket is not connected.
        """
        if not self.is_connected:
            raise Exception("Socket not connected")
        self.send_queue.put(data)

    def receive(self) -> bytes:
        """
        Waits and returns data from the receive queue.
        Raises an exception if the socket is disconnected.
        """
        if not self.is_connected:
            raise Exception("Socket not connected")
        while self.is_connected:
            try:
                return self.recv_queue.get(timeout=0.2)
            except Empty:
                continue
        raise Exception("Connection closed")

    def close(self) -> None:
        """
        Cleanly closes the connection, stopping threads and closing peer sockets.
        """
        if not self.is_connected:
            return
        self.is_connected = False
        self.stop_event.set()  # Signal threads to stop

        self.peer_receive.close()
        self.peer_send.close()

        if self.sender_thread.is_alive():
            self.sender_thread.join(timeout=1)
        if self.receiver_thread.is_alive():
            self.receiver_thread.join(timeout=1)
        print("Connection closed.")

    def __send_loop(self):
        """
        Main loop for the sending thread.
        Handles Diffie-Hellman key exchange to establish encryption key,
        encrypts data, hides it in images using steganography,
        splits images into parts, packages into a zip, and sends.
        """
        p = random_prime_number()
        g = find_primitive_root(p)
        private_key = generate_5_digit_number()
        self.peer_send = Peer2Peer(self.peer_ip, 5008, 5007)

        send_key = DH_Endpoint(p, g, private_key)
        public_key = send_key.generate_public_key()

        # Convert integers to bytes for transmission
        p = int_to_bytes(p)
        g = int_to_bytes(g)
        public_key = int_to_bytes(public_key)

        # Send DH parameters and public key to receiver
        self.peer_send.send_message(p)
        self.peer_send.send_message(g)
        self.peer_send.send_message(public_key)

        # Receive the receiver's public key
        key_public_receiver = self.peer_send.get_message()
        key_public_receiver = bytes_to_int(key_public_receiver)

        # Generate shared secret key
        key = int_to_bytes(send_key.generate_full_key(key_public_receiver))

        while not self.stop_event.is_set():
            try:
                content = self.send_queue.get(timeout=1)[:MAX_CONTENT_LENGTH]
            except Empty:
                continue

            # Create temporary directory to store image parts and files
            temp_directory = create_random_name_directory(16, get_temp_dir())

            # Encrypt the content with AES using the shared key
            cipher = AESCipher(key)
            encrypted_content = cipher.encrypt(content.decode('utf-16'))

            # Generate a random image as a carrier
            image_path = temp_directory / generate_random_filename(16, 'png')
            generate_random_image(image_path)

            # Hide the encrypted content inside the image
            temp_img_with_hidden_content_path = temp_directory / generate_random_filename(16, 'png')
            hide_message_in_image(image_path, encrypted_content, temp_img_with_hidden_content_path)

            # Split the steganographed image into parts
            images_matrix = split_image(temp_img_with_hidden_content_path)
            parts_paths = []

            # Add metadata (row, column) to each image part and save
            for i, row in enumerate(images_matrix):
                for j, image in enumerate(row):
                    part_path = temp_directory / generate_random_filename(16, 'png')
                    parts_paths.append(part_path)
                    add_metadata_to_image(image, row_and_column_to_str(i, j), part_path)

            # Create a zip file containing all image parts
            parts_zip_path = temp_directory / generate_random_filename(16, 'zip')
            create_zip_file(parts_paths, parts_zip_path)

            # Send the zip file containing image parts to the peer
            self.peer_send.send_file(parts_zip_path)

            # Clean up temporary files and directory
            shutil.rmtree(temp_directory)

        self.peer_send.close()

    def __safe_receive_loop(self):
        """
        Wrapper around __receive_loop to handle exceptions
        and properly set flags when errors occur.
        """
        try:
            self.__receive_loop()
        except:
            self.stop_event.set()
            self.is_connected = False

    def __safe_send_loop(self):
        """
        Wrapper around __send_loop to handle exceptions
        and properly set flags when errors occur.
        """
        try:
            self.__send_loop()
        except:
            self.stop_event.set()
            self.is_connected = False

    def __receive_loop(self):
        """
        Main loop for the receiver thread.
        Performs Diffie-Hellman key exchange to establish shared key,
        receives zip files of image parts,
        reconstructs images and extracts the hidden encrypted message,
        then decrypts and puts the content into the receive queue.
        """
        key_private = generate_5_digit_number()
        self.peer_receive = Peer2Peer(self.peer_ip, 5007, 5008)

        # Receive DH parameters and sender's public key
        p = self.peer_receive.get_message()
        g = self.peer_receive.get_message()
        key_public_sender = self.peer_receive.get_message()

        p = bytes_to_int(p)
        g = bytes_to_int(g)
        key_public_sender = bytes_to_int(key_public_sender)

        # Generate receiver's DH key pair
        receive_key = DH_Endpoint(p, g, key_private)
        public_key = receive_key.generate_public_key()

        # Send public key back to sender
        public_key = int_to_bytes(public_key)
        self.peer_receive.send_message(public_key)

        # Generate shared secret key
        key = int_to_bytes(receive_key.generate_full_key(key_public_sender))

        while not self.stop_event.is_set():
            # Create temporary directory for received files
            temp_directory = create_random_name_directory(16, get_temp_dir())

            parts_zip_path = temp_directory / generate_random_filename(16, 'zip')

            # Receive the zip file containing the image parts
            self.peer_receive.get_file(parts_zip_path)

            # Extract the zip to a subdirectory
            parts_directory = create_random_name_directory(16, temp_directory)
            extract_zip_file(parts_zip_path, parts_directory)

            metadata_images = []

            # Read metadata and load each image part
            for file in os.listdir(parts_directory):
                file_path = parts_directory / file
                index_str = read_metadata_from_image(file_path)

                img = Image.open(file_path)
                row, col = str_to_row_and_column(index_str)
                metadata_images.append(SplittedImageInfo(row, col, img))

            # Sort images by row and column to restore original order
            metadata_images.sort(key=lambda info: (info.row, info.column))

            num_of_rows = metadata_images[-1].row + 1
            num_of_cols = metadata_images[-1].column + 1

            parts_matrix = []

            # Rebuild the matrix of image parts
            img_index = 0
            for i in range(num_of_rows):
                row = []
                for j in range(num_of_cols):
                    row.append(metadata_images[img_index].image)
                    img_index += 1
                parts_matrix.append(row)

            # Restore the full image from parts
            restored_img_path = temp_directory / generate_random_filename(16, 'png')
            restore_image(parts_matrix, restored_img_path)

            # Reveal the encrypted message hidden in the image
            encrypted_content = reveal_message_from_image(restored_img_path)

            # Decrypt the content using AES with the shared key
            cipher = AESCipher(key)
            content = cipher.decrypt(encrypted_content)

            # Put the decrypted content in the receive queue
            self.recv_queue.put(content.encode('utf-16'))

            # Clean up temporary files and directory
            shutil.rmtree(temp_directory)

        self.peer_receive.close()
