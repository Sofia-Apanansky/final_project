from dataclasses import dataclass

from PIL.ImageFile import ImageFile


# SplittedImageInfo is a data container that holds information about a sub-image (tile)
# from a larger image that has been split into rows and columns.
@dataclass
class SplittedImageInfo:
    # The row index of the sub-image in the original image grid
    row: int

    # The column index of the sub-image in the original image grid
    column: int

    # The actual image tile
    image: ImageFile
