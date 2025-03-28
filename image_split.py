from pathlib import Path

from PIL import Image
from PIL.ImageFile import ImageFile


def split_image(image_filepath: str | Path, rows: int = 6, cols: int = 8) -> list[list[ImageFile]]:
    # Open the image
    image_path = Path(image_filepath).resolve()
    image_filename = image_path.stem
    img = Image.open(image_path)
    img_width, img_height = img.size

    # Calculate the width and height of each part
    part_width = img_width // cols
    part_height = img_height // rows

    output_directory = image_path.parent

    output_images = []

    for row in range(rows):
        output_images.append([])
        for col in range(cols):
            # Define the bounding box for each part
            left = col * part_width
            upper = row * part_height
            right = min((col + 1) * part_width, img_width)
            lower = min((row + 1) * part_height, img_height)

            # Crop the image to get the part
            part = img.crop((left, upper, right, lower))
            output_images[row].append(part)

    return output_images


def restore_image(parts_image_matrix: list[list[ImageFile]], output_filepath: str | Path) -> None:
    rows = len(parts_image_matrix)
    cols = len(parts_image_matrix[0])

    image_width, image_height = 0, 0
    for row in range(rows):
        for col in range(cols):
            width, height = parts_image_matrix[row][col].size
            image_width += width
            image_height += height
    image_size = image_width // rows, image_height // cols

    # Create a new blank image with the original size
    restored_image = Image.new('RGB', image_size)

    part_width = image_size[0] // cols
    part_height = image_size[1] // rows

    # Iterate through each part and paste it into the correct position
    for row in range(rows):
        for col in range(cols):
            # Define where to paste the current part
            left = col * part_width
            upper = row * part_height
            restored_image.paste(parts_image_matrix[row][col], (left, upper))

    restored_image.save(Path(output_filepath))
