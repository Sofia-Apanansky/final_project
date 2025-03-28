import shutil
from typing import Final

from aes_cipher import AESCipher
from random_image import generate_random_image
from p2p import Peer2Peer
from steganography import hide_message_in_image
from image_split import split_image
from image_metadata import add_metadata_to_image
from utils import generate_random_filename, row_and_column_to_str, get_project_directory, create_random_name_directory
from zip_files import create_zip_file

MAX_CONTENT_LENGTH: Final[int] = 115167


def start_user_send(peer_ip: str) -> None:
    user_send_loop(peer_ip)


def user_send_loop(peer_ip: str) -> None:
    # key = random.randbytes(32)  # TODO consider how to generate the key
    key = b'1' * 32
    peer_send = Peer2Peer(peer_ip, 5008, 5007)
    peer_send.send_message(key)

    while True:
        temp_directory = create_random_name_directory(16, get_project_directory())

        content = input("Write content: ")[:MAX_CONTENT_LENGTH]

        cipher = AESCipher(key)
        encrypted_content = cipher.encrypt(content)

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
