from base64 import b64decode
from pathlib import Path

import requests
from PIL import Image

from utils import generate_random_color, jpg_to_png

API_KEY = ""  # Fixme store in another place
API_NINJAS_RANDOM_IMAGE_ENDPOINT = "https://api.api-ninjas.com/v1/randomimage?width={width}&height={height}"

headers = {"X-Api-Key": API_KEY}


def fetch_image_from_api(width: int, height: int) -> bytes:
    formatted_endpoint = API_NINJAS_RANDOM_IMAGE_ENDPOINT.format(width=width, height=height)
    response = requests.get(formatted_endpoint, headers=headers)
    if response.status_code != 200:
        return b''

    img_base64 = response.content

    img_bytes = b64decode(img_base64)
    return img_bytes


def generate_random_image(output_image_path: str | Path, width: int = 640, height: int = 480) -> None:
    img_bytes = fetch_image_from_api(width, height)
    if not img_bytes:
        default_img = Image.new("RGB", (width, height), color=generate_random_color())
        default_img.save(output_image_path, format="PNG")
        return

    png_img_bytes = jpg_to_png(img_bytes)
    with open(output_image_path, 'wb') as f:
        f.write(png_img_bytes)
