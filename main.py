import os
import random
import string

from aes_cipher import AESCipher
from steganography import hide_message_in_image
from image_split import split_image
from image_metadata import add_metadata_to_image
from zip_files import create_zip_file

from zip_files import extract_zip_file
from image_metadata import read_metadata_from_image


def generate_random_filename(n: int, ext: str = '') -> str:
    name = ''.join(random.choices(string.ascii_letters + string.digits, k=n))
    if ext:
        name += '.' + ext
    return name


def is_png_file(file_path: str) -> bool:
    return file_path.endswith('.png')

#
# def count_images_in_folder(folder_path: str) -> int:
#     files = os.listdir(folder_path)
#     image_count = len([file for file in files if is_png_file(file)])
#     return image_count
#

def main() -> None:
    password = input("Write password: ")
    key = random.randbytes(32)
    cipher = AESCipher(key)
    new_password = cipher.encrypt(password)

    image_path = "poto-1.jpg"  # TODO change
    new_path = "new_path.png"  # TODO change
    hide_message_in_image(image_path, new_password, new_path)

    row = int(input("Write row: "))
    cols = int(input("Write cols: "))
    images_matrix = split_image(new_path, row, cols)

    filenames = []

    for i, row in enumerate(images_matrix):
        for j, image in enumerate(row):
            filename = generate_random_filename(16, 'png')
            filenames.append(filename)
            add_metadata_to_image(image, f"{i}_{j}", filename)

    name_zip_file = generate_random_filename(16, 'zip')
    create_zip_file(filenames, name_zip_file)
    for f in filenames:
        os.remove(f)


def main_user_extract() -> None:
    name_zip_to_extract = "LFwsHqPSzYsbqlCB.zip"
    name_zip_after_extraction = "zip_after_extraction"
    extract_zip_file(name_zip_to_extract, name_zip_after_extraction)

    number_of_images_in_file = len(os.listdir('zip_after_extraction'))

    # for file in os.listdir(name_zip_to_extract):
    #     if not is_png_file(file):
    #         continue
    #     read_metadata_from_image(file


if __name__ == '__main__':
    main_user_extract()
