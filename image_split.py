from pathlib import Path

from PIL import Image
from PIL.ImageFile import ImageFile

# Splits an image into a grid of rows × cols and returns the parts as a 2D list
def split_image(image_filepath: str | Path, rows: int = 6, cols: int = 8) -> list[list[ImageFile]]:
    # Resolve the full path and extract the file stem (name without extension)
    image_path = Path(image_filepath).resolve()
    image_filename = image_path.stem

    # Open the image using PIL
    img = Image.open(image_path)
    img_width, img_height = img.size

    # Calculate the width and height of each image part
    part_width = img_width // cols
    part_height = img_height // rows

    # The list that will hold the 2D array of cropped image parts
    output_images = []

    # Loop over each row and column to crop the image
    for row in range(rows):
        output_images.append([])  # Create a new row
        for col in range(cols):
            # Compute the coordinates of the crop box
            left = col * part_width
            upper = row * part_height
            right = min((col + 1) * part_width, img_width)
            lower = min((row + 1) * part_height, img_height)

            # Crop the image using the bounding box
            part = img.crop((left, upper, right, lower))
            # Store the cropped part in the 2D list
            output_images[row].append(part)

    return output_images

# Restores a full image from a 2D matrix of image parts and saves it to a file
def restore_image(parts_image_matrix: list[list[ImageFile]], output_filepath: str | Path) -> None:
    # Get number of rows and columns from the matrix
    rows = len(parts_image_matrix)
    cols = len(parts_image_matrix[0])

    # Estimate the full image size by summing dimensions of parts
    image_width, image_height = 0, 0
    for row in range(rows):
        for col in range(cols):
            width, height = parts_image_matrix[row][col].size
            image_width += width
            image_height += height

    # Compute the average size of the original image
    image_size = image_width // rows, image_height // cols

    # Create a new blank image to paste the parts into
    restored_image = Image.new('RGB', image_size)

    # Calculate the width and height of each part (should match original parts)
    part_width = image_size[0] // cols
    part_height = image_size[1] // rows

    # Paste each image part into the correct position
    for row in range(rows):
        for col in range(cols):
            # Calculate top-left corner where this part should be pasted
            left = col * part_width
            upper = row * part_height
            restored_image.paste(parts_image_matrix[row][col], (left, upper))

    # Save the reassembled image to the specified path
    restored_image.save(Path(output_filepath))
