import os
from PIL import Image
from data_info import SplittedImageInfo
from utils import str_to_row_and_column
from zip_files import extract_zip_file
from image_metadata import read_metadata_from_image
from image_split import restore_image


def main_user_receive() -> None:
    file_zip_to_extract = "LFwsHqPSzYsbqlCB.zip"  # מקבלת זאת בשליחה של התקשורת
    file_zip_after_extraction = "zip_after_extraction"
    extract_zip_file(file_zip_to_extract, file_zip_after_extraction)
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

    restore_image(parts_matrix, 'my_img.png')
#    print(reveal_message_from_image('my_img.png'))
# need to get the key
#    key = ...
#    cipher = AESCipher(key)
#    new_password = cipher.decrypt(reveal_message_from_image('my_img.png'))
