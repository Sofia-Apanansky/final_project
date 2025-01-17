import random
import string
import zipfile

from aes_cipher import AESCipher
from steganography import hide_message_in_image
from image_split import split_image
from image_metadata import add_metadata_to_image


def generate_random_filename(n: int, ext: str = '') -> str:
    name = ''.join(random.choices(string.ascii_letters + string.digits, k=n))
    if ext:
        name += '.' + ext
    return name


def main() -> None:
    password = input("write password")
    key = random.randbytes(32)
    cipher = AESCipher(key)
    new_password = cipher.encrypt(password)

    image_path = "poto-1.jpg"
    new_path = "new_path.png"
    hide_message_in_image(image_path, new_password, new_path)

    row = int(input("write row"))
    cols = int(input("write cols"))
    images_matrix = split_image(new_path, row, cols)

    filenames = []

    for i, row in enumerate(images_matrix):
        for j, image in enumerate(row):
            filename = generate_random_filename(16, 'png')
            filenames.append(filename)
            add_metadata_to_image(image, f"{i}_{j}", filename)




if __name__ == '__main__':
    main()
