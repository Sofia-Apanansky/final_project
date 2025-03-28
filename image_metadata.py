from pathlib import Path
from PIL import Image
from PIL.ImageFile import ImageFile
from PIL.PngImagePlugin import PngInfo


def add_metadata_to_image(image: ImageFile, metadata: str, output_image_filepath: str | Path) -> None:
    png_info = PngInfo()
    png_info.add_text('Description', metadata)
    image.save(output_image_filepath, pnginfo=png_info)


def read_metadata_from_image(image_filepath: str | Path) -> str:
    image = Image.open(image_filepath)
    image_info = image.info
    metadata = image_info['Description']
    return metadata
