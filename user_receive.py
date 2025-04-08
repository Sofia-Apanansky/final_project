import os
import shutil

from PIL import Image

from aes_cipher import AESCipher
from data_info import SplittedImageInfo
from p2p import Peer2Peer
from steganography import reveal_message_from_image
from utils import str_to_row_and_column, create_random_name_directory, get_project_directory, generate_random_filename,random_prime_number, int_to_bytes, bytes_to_int
from zip_files import extract_zip_file
from image_metadata import read_metadata_from_image
from image_split import restore_image
from dh_key_exchange import DH_Endpoint



def start_user_receive(peer_ip: str) -> None:
    user_receive_loop(peer_ip)


def user_receive_loop(peer_ip: str) -> None:
    key_private =random_prime_number()
    peer_receive = Peer2Peer(peer_ip, 5007, 5008)

    p=peer_receive.get_message()
    g=peer_receive.get_message()
    key_public_sender = peer_receive.get_message()

    p=bytes_to_int(p)
    g=bytes_to_int(g)
    key_public_sender=bytes_to_int(key_public_sender)

    receive_key=DH_Endpoint(p,g,key_private)
    public_key=receive_key.generate_public_key()

    public_key=int_to_bytes(public_key)
    peer_receive.send_message(public_key)

    key= int_to_bytes(receive_key.generate_full_key(key_public_sender))


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

        print(f"Content: {content}")

        shutil.rmtree(temp_directory)
