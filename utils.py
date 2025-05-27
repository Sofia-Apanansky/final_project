import random
import string
from io import BytesIO
from pathlib import Path
from sympy import isprime, primitive_root
from PIL import Image


def get_project_directory() -> Path:
    return Path(__file__).parent


def generate_random_filename(n: int, ext: str = '') -> str:
    name = ''.join(random.choices(string.ascii_letters + string.digits, k=n))
    if ext:
        name += '.' + ext
    return name


def is_png_file(file_path: str) -> bool:
    return file_path.endswith('.png')


def row_and_column_to_str(row: int, col: int) -> str:
    return f'{row}_{col}'


def str_to_row_and_column(index_str) -> tuple[int, int]:
    splitted_indices = index_str.split('_')
    row, col = splitted_indices
    return int(row), int(col)


def create_random_name_directory(n: int, directory_parent: Path) -> Path:
    dir_path = directory_parent / generate_random_filename(n)
    dir_path.mkdir()
    return dir_path


def jpg_to_png(jpg_bytes: bytes) -> bytes:
    img = Image.open(BytesIO(jpg_bytes))

    # Convert to PNG format in memory
    png_bytes_io = BytesIO()
    img.save(png_bytes_io, format="PNG")

    return png_bytes_io.getvalue()


def generate_random_color() -> tuple[int, int, int]:
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    return r, g, b


def random_prime_number(min_digits=3, max_digits=5):
    min_value = 10 ** (min_digits - 1)
    max_value = 10 ** max_digits - 1
    primes = []
    for num in range(min_value, max_value + 1):
        if num < 2:
            continue
        is_prime = True
        for i in range(2, int(num ** 0.5) + 1):
            if num % i == 0:
                is_prime = False
                break
        if is_prime:
            primes.append(num)
    return random.choice(primes) if primes else None

def find_primitive_root(p):
    if not isprime(p):
        raise ValueError("p must be a prime number.")
    return primitive_root(p)

def int_to_bytes(number: int) -> bytes:
    num_bytes = (number.bit_length() + 7) // 8
    b = number.to_bytes(num_bytes, byteorder='little')
    return b


def bytes_to_int(num: bytes) -> int:
    k = int.from_bytes(num, byteorder='little')
    return k
