import os
import shutil
from queue import Queue
from threading import Thread
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
from utils import (bytes_to_int, create_random_name_directory, generate_random_filename, get_project_directory,
                   int_to_bytes, random_prime_number, row_and_column_to_str, str_to_row_and_column)
from zip_files import create_zip_file, extract_zip_file

MAX_CONTENT_LENGTH: Final[int] = 115167


class PictureEncryptionSocket:
    def __init__(self, peer_ip: str) -> None:
        self.stop_event = None
        self.peer_ip = peer_ip
        self.send_queue = Queue()
        self.recv_queue = Queue()
        self.sender_thread = Thread()
        self.receiver_thread = Thread()
        self.is_connected = False

    def connect(self) -> None:
        self.sender_thread = Thread(target=self.__send_loop)
        self.receiver_thread = Thread(target=self.__receive_loop)

        self.sender_thread.start()
        self.receiver_thread.start()

        self.is_connected = True

    def send(self, data: bytes) -> None:
        if not self.is_connected:
            raise Exception("Socket not connected")
        self.send_queue.put(data)

    def receive(self) -> bytes:
        if not self.is_connected:
            raise Exception("Socket not connected")
        return self.recv_queue.get()

    def close(self) -> None:
        if not self.is_connected:
            return
        self.is_connected = False
        self.stop_event.set()  # Signal threads to stop

        self.send_queue.put(None)
        self.recv_queue.put(b'')

        if self.sender_thread.is_alive():
            self.sender_thread.join(timeout=1)
        if self.receiver_thread.is_alive():
            self.receiver_thread.join(timeout=1)
        print("Connection closed.")

#    def shutdown(self, socket:int) -> None:
#        self.stop_event.set()

#        if self.sender_thread.is_alive():
#            self.send_queue.put(None)  # Unblock sender thread if waiting
#            self.sender_thread.join(timeout=1)
#            print("[INFO] Sender thread stopped.")

#        if self.receiver_thread.is_alive():
#            self.receiver_thread.join(timeout=1)
#            print("[INFO] Receiver thread stopped.")

    def __send_loop(self):
        p = random_prime_number()
        g = random_prime_number()
        private_key = random_prime_number()
        peer_send = Peer2Peer(self.peer_ip, 5008, 5007)

        send_key = DH_Endpoint(p, g, private_key)
        public_key = send_key.generate_public_key()

        p = int_to_bytes(p)
        g = int_to_bytes(g)
        public_key = int_to_bytes(public_key)

        peer_send.send_message(p)
        peer_send.send_message(g)
        peer_send.send_message(public_key)

        key_public_receiver = peer_send.get_message()  # public_key_receiver
        key_public_receiver = bytes_to_int(key_public_receiver)
        key = int_to_bytes(send_key.generate_full_key(key_public_receiver))

        while True:
            temp_directory = create_random_name_directory(16, get_project_directory())

            content = self.send_queue.get()[:MAX_CONTENT_LENGTH]

            cipher = AESCipher(key)
            encrypted_content = cipher.encrypt(content.decode())

            image_path = temp_directory / generate_random_filename(16, 'png')
            generate_random_image(image_path)

            temp_img_with_hidden_content_path = temp_directory / generate_random_filename(16, 'png')
            hide_message_in_image(image_path, encrypted_content, temp_img_with_hidden_content_path)

            images_matrix = split_image(temp_img_with_hidden_content_path)
            parts_paths = []

            for i, row in enumerate(images_matrix):
                for j, image in enumerate(row):
                    part_path = temp_directory / generate_random_filename(16, 'png')
                    parts_paths.append(part_path)
                    add_metadata_to_image(image, row_and_column_to_str(i, j), part_path)

            parts_zip_path = temp_directory / generate_random_filename(16, 'zip')
            create_zip_file(parts_paths, parts_zip_path)

            peer_send.send_file(parts_zip_path)  # send the zip in parts

            shutil.rmtree(temp_directory)

    def __receive_loop(self):
        key_private = random_prime_number()
        peer_receive = Peer2Peer(self.peer_ip, 5007, 5008)

        p = peer_receive.get_message()
        g = peer_receive.get_message()
        key_public_sender = peer_receive.get_message()

        p = bytes_to_int(p)
        g = bytes_to_int(g)
        key_public_sender = bytes_to_int(key_public_sender)

        receive_key = DH_Endpoint(p, g, key_private)
        public_key = receive_key.generate_public_key()

        public_key = int_to_bytes(public_key)
        peer_receive.send_message(public_key)

        key = int_to_bytes(receive_key.generate_full_key(key_public_sender))

        while True:
            temp_directory = create_random_name_directory(16, get_project_directory())

            parts_zip_path = temp_directory / generate_random_filename(16, 'zip')

            peer_receive.get_file(parts_zip_path)

            parts_directory = create_random_name_directory(16, temp_directory)

            extract_zip_file(parts_zip_path, parts_directory)

            metadata_images = []
            for file in os.listdir(parts_directory):
                file_path = parts_directory / file
                index_str = read_metadata_from_image(file_path)

                img = Image.open(file_path)
                row, col = str_to_row_and_column(index_str)
                metadata_images.append(SplittedImageInfo(row, col, img))

            metadata_images.sort(key=lambda info: (info.row, info.column))

            num_of_rows = metadata_images[-1].row + 1
            num_of_cols = metadata_images[-1].column + 1

            parts_matrix = []

            img_index = 0
            for i in range(num_of_rows):
                row = []
                for j in range(num_of_cols):
                    row.append(metadata_images[img_index].image)
                    img_index += 1
                parts_matrix.append(row)

            restored_img_path = temp_directory / generate_random_filename(16, 'png')
            restore_image(parts_matrix, restored_img_path)

            encrypted_content = reveal_message_from_image(restored_img_path)

            cipher = AESCipher(key)
            content = cipher.decrypt(encrypted_content)

            self.recv_queue.put(content.encode())

            shutil.rmtree(temp_directory)
