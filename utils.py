import random
import string
from io import BytesIO
from pathlib import Path
from tempfile import gettempdir

from PIL import Image
from sympy import isprime, primitive_root

# Returns the system temporary directory as a Path object
def get_temp_dir() -> Path:
    return Path(gettempdir())

# Generates a random filename of length `n` with an optional extension `ext`
def generate_random_filename(n: int, ext: str = '') -> str:
    name = ''.join(random.choices(string.ascii_letters + string.digits, k=n))
    if ext:
        name += '.' + ext
    return name

# Checks whether the file has a .png extension
def is_png_file(file_path: str) -> bool:
    return file_path.endswith('.png')

# Converts row and column indices to a string representation ("2_3")
def row_and_column_to_str(row: int, col: int) -> str:
    return f'{row}_{col}'

# Parses a string in the format "row_col" back into a tuple of integers
def str_to_row_and_column(index_str) -> tuple[int, int]:
    splitted_indices = index_str.split('_')
    row, col = splitted_indices
    return int(row), int(col)

# Creates a new directory with a random name of length `n` inside a given parent directory
def create_random_name_directory(n: int, directory_parent: Path) -> Path:
    dir_path = directory_parent / generate_random_filename(n)
    dir_path.mkdir()
    return dir_path

# Converts image data from JPG format to PNG format
def jpg_to_png(jpg_bytes: bytes) -> bytes:
    img = Image.open(BytesIO(jpg_bytes))  # Open JPG image from bytes
    png_bytes_io = BytesIO()
    img.save(png_bytes_io, format="PNG")  # Save as PNG to memory
    return png_bytes_io.getvalue()

# Generates a random RGB color tuple
def generate_random_color() -> tuple[int, int, int]:
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    return r, g, b

# Generates a random 5-digit integer (for use as private keys)
def generate_5_digit_number() -> int:
    return random.randint(10000, 99999)

# Returns a random prime number between a range of digit lengths
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
    # Return a randomly selected prime from the list
    return random.choice(primes) if primes else None

# Finds a primitive root modulo a prime number `p`
def find_primitive_root(p):
    if not isprime(p):
        raise ValueError("p must be a prime number.")
    return primitive_root(p)

# Converts an integer to bytes using little-endian encoding
def int_to_bytes(number: int) -> bytes:
    num_bytes = (number.bit_length() + 7) // 8  # Calculate the number of bytes needed
    b = number.to_bytes(num_bytes, byteorder='little')
    return b

# Converts bytes to an integer using little-endian encoding
def bytes_to_int(num: bytes) -> int:
    k = int.from_bytes(num, byteorder='little')
    return k
