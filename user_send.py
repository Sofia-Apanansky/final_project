import os
import random
from pathlib import Path

from aes_cipher import AESCipher
from steganography import hide_message_in_image
from image_split import split_image
from image_metadata import add_metadata_to_image
from utils import generate_random_filename, row_and_column_to_str, get_project_directory
from zip_files import create_zip_file


def main_user_send() -> None:
    key = random.randbytes(32)  # TODO consider how to generate the key
    # TODO init sender socket

    temp_directory = get_project_directory() / generate_random_filename(16)
    temp_directory.mkdir()

    while True:
        content = input("Write content: ")
        # TODO send the key over the socket
        cipher = AESCipher(key)
        encrypted_content = cipher.encrypt(content)

        # image_path = generate_image()
        image_path = Path("poto-1.jpg").resolve()  # FIXME testing only

        temp_img_with_hidden_content_path = generate_random_filename(16, 'png')
        hide_message_in_image(image_path, encrypted_content, temp_img_with_hidden_content_path)

        row = int(input("Write row: "))  # TODO consider to set as constant
        cols = int(input("Write cols: "))  # TODO consider to set as constant
        images_matrix = split_image(temp_img_with_hidden_content_path, row, cols)

        parts_paths = []

        for i, row in enumerate(images_matrix):
            for j, image in enumerate(row):
                part_path = get_project_directory() / generate_random_filename(16, 'png')
                parts_paths.append(part_path)
                add_metadata_to_image(image, row_and_column_to_str(i, j), part_path)

        parts_zip_path = get_project_directory() / generate_random_filename(16, 'zip')
        create_zip_file(parts_paths, parts_zip_path)

        # TODO send zip over tcp socket

        for f in parts_paths:
            f.unlink()  # Delete part

        parts_zip_path.unlink()  # Delete zip
