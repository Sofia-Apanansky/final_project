import os
from time import sleep

from PIL import Image

from aes_cipher import AESCipher
from data_info import SplittedImageInfo
from p2p import Peer2Peer
from steganography import reveal_message_from_image
from utils import str_to_row_and_column, create_random_name_directory, get_project_directory, generate_random_filename
from zip_files import extract_zip_file
from image_metadata import read_metadata_from_image
from image_split import restore_image


def main_user_receive() -> None:
    peer_receive = Peer2Peer('127.0.0.1', 5007, 5008)

    key = peer_receive.get_message()

    while True:
        temp_directory = create_random_name_directory(16, get_project_directory())

        parts_zip_path = temp_directory / generate_random_filename(16, 'zip')

        peer_receive.get_file(parts_zip_path)  # ...

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

        print(f"Content: {content}")
