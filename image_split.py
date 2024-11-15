import os
from collections import Counter

from PIL import Image
from PIL.ImageFile import ImageFile


def resolve_output_dir(given_output_dir: str) -> str:
    if given_output_dir is not None:
        if not os.path.exists(given_output_dir):
            os.makedirs(given_output_dir)
        return given_output_dir
    else:
        return "./"


def square_image(image: ImageFile) -> ImageFile:
    im_width, im_height = image.size

    min_dimension = min(im_width, im_height)
    max_dimension = max(im_width, im_height)
    bg_color = determine_bg_color(image)
    squared_img = Image.new("RGB", (max_dimension, max_dimension), bg_color)
    offset = int((max_dimension - min_dimension) / 2)
    if im_width > im_height:
        squared_img.paste(image, (0, offset))
    else:
        squared_img.paste(image, (offset, 0))

    return squared_img


def determine_bg_color(im: ImageFile):
    im_width, im_height = im.size
    rgb_im = im.convert('RGBA')
    all_colors = []
    areas = [[(0, 0), (im_width, im_height / 10)],
             [(0, 0), (im_width / 10, im_height)],
             [(im_width * 9 / 10, 0), (im_width, im_height)],
             [(0, im_height * 9 / 10), (im_width, im_height)]]
    for area in areas:
        start = area[0]
        end = area[1]
        for x in range(int(start[0]), int(end[0])):
            for y in range(int(start[1]), int(end[1])):
                pix = rgb_im.getpixel((x, y))
                all_colors.append(pix)
    return Counter(all_colors).most_common(1)[0][0]


def split_image(image_path: str, rows: int, cols: int, should_square: bool, output_dir: str = None) -> None:
    im = Image.open(image_path)
    im_width, im_height = im.size
    row_width = int(im_width / cols)
    row_height = int(im_height / rows)

    name, ext = os.path.splitext(image_path)
    name = os.path.basename(name)

    output_dir = resolve_output_dir(output_dir)

    if should_square:
        squared_im = square_image(im)
        im = squared_im
        im_width, im_height = im.size
        row_width = int(im_width / cols)
        row_height = int(im_height / rows)

    n = 0
    for i in range(rows):
        for j in range(cols):
            box = (j * row_width, i * row_height,
                   j * row_width + row_width, i * row_height + row_height)
            outp = im.crop(box)
            outp_path = name + "_" + str(n) + ext
            outp_path = os.path.join(output_dir, outp_path)
            outp.save(outp_path)
            n += 1


def reverse_split(paths_to_merge: tuple[str], rows: int, cols: int, image_path: str, should_cleanup: bool):
    ...  # TODO
