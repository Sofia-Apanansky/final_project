from dataclasses import dataclass
from PIL.ImageFile import ImageFile


@dataclass
class SplittedImageInfo:
    row: int
    column : int
    image: ImageFile
