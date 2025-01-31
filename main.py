import os
import random
import string
import re
from importlib.metadata import metadata

from PIL import Image
from numpy.ma.core import append

import data_info
from aes_cipher import AESCipher
from steganography import hide_message_in_image
from image_split import split_image
from image_metadata import add_metadata_to_image
from zip_files import create_zip_file
from data_info import SplittedImageInfo

from zip_files import extract_zip_file
from image_metadata import read_metadata_from_image
from image_split import restore_image


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

def row_and_column_to_str(row: int, col: int) -> str:
    return f'{row}_{col}'


def str_to_row_and_column(index_str) -> tuple[int, int]:
    splitted_indices = index_str.split('_')
    row, col = splitted_indices
    return int(row), int(col)


def main() -> None:
    password = input("Write password: ")
    key = random.randbytes(32)
    cipher = AESCipher(key)
    new_password = cipher.encrypt(password)

    image_path = "poto-1.jpg"  # TODO change
    new_path = "new_path22.png"  # TODO change
    hide_message_in_image(image_path, new_password, new_path)

    row = int(input("Write row: "))
    cols = int(input("Write cols: "))
    images_matrix = split_image(new_path, row, cols)

    filenames = []

    for i, row in enumerate(images_matrix):
        for j, image in enumerate(row):
            filename = generate_random_filename(16, 'png')
            filenames.append(filename)
            add_metadata_to_image(image, row_and_column_to_str(i, j), filename)

    # for t in range(4):
    #   print(read_metadata_from_image(filenames[t]))

    name_zip_file = generate_random_filename(16, 'zip')
    create_zip_file(filenames, name_zip_file)
    for f in filenames:
        os.remove(f)


# ............................................................................................
def main_user_extract() -> None:
    # file_zip_to_extract = "LFwsHqPSzYsbqlCB.zip" #מקבלת זאת בשליחה של התקשורת
    file_zip_after_extraction = "zip_after_extraction"
    # extract_zip_file(file_zip_to_extract, file_zip_after_extraction)
    metadata_images = []
    for file in os.listdir(file_zip_after_extraction):
        file_path = file_zip_after_extraction + "\\" + file
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

    print(parts_matrix)

    restore_image(parts_matrix, 'my_img.png')


if __name__ == '__main__':
    main_user_extract()
