from pathlib import Path

from PIL import Image
from PIL.ImageFile import ImageFile
from PIL.PngImagePlugin import PngInfo

# Adds textual metadata to a PNG image and saves it to a specified file path
def add_metadata_to_image(image: ImageFile, metadata: str, output_image_filepath: str | Path) -> None:
    # Create a PNG metadata container
    png_info = PngInfo()
    # Add the metadata string under the key 'Description'
    png_info.add_text('Description', metadata)
    # Save the image with the added metadata
    image.save(output_image_filepath, pnginfo=png_info)

# Reads and returns the 'Description' metadata from a PNG image
def read_metadata_from_image(image_filepath: str | Path) -> str:
    # Open the image from the given file path
    image = Image.open(image_filepath)
    # Access the image metadata dictionary
    image_info = image.info
    # Retrieve the value stored under the 'Description' key
    metadata = image_info['Description']
    return metadata
