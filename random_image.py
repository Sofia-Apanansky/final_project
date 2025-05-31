from base64 import b64decode
from pathlib import Path

import requests
from PIL import Image

from utils import generate_random_color, jpg_to_png

API_KEY = ""  # Fixme store in another place
API_NINJAS_RANDOM_IMAGE_ENDPOINT = "https://api.api-ninjas.com/v1/randomimage?width={width}&height={height}"

headers = {"X-Api-Key": API_KEY}

# Fetches an image from the API Ninjas random image endpoint as raw bytes
def fetch_image_from_api(width: int, height: int) -> bytes:
    # Format the endpoint URL with requested image dimensions
    formatted_endpoint = API_NINJAS_RANDOM_IMAGE_ENDPOINT.format(width=width, height=height)
    # Make the HTTP GET request with API key header
    response = requests.get(formatted_endpoint, headers=headers)
    # If the response is unsuccessful, return empty bytes
    if response.status_code != 200:
        return b''

    # The API returns base64-encoded image data in the response content
    img_base64 = response.content

    # Decode the base64 string into raw image bytes
    img_bytes = b64decode(img_base64)
    return img_bytes

# Generates a random image and saves it to the given path, falling back to a solid color if the API fails
def generate_random_image(output_image_path: str | Path, width: int = 640, height: int = 480) -> None:
    # Try fetching image bytes from the API
    img_bytes = fetch_image_from_api(width, height)
    # If the API fetch failed, generate a solid-color image as fallback
    if not img_bytes:
        default_img = Image.new("RGB", (width, height), color=generate_random_color())
        default_img.save(output_image_path, format="PNG")
        return

    # Convert the downloaded JPG bytes to PNG format bytes
    png_img_bytes = jpg_to_png(img_bytes)
    # Write the PNG image bytes to the output file
    with open(output_image_path, 'wb') as f:
        f.write(png_img_bytes)
