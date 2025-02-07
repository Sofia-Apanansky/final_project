from pathlib import Path

from stegano import lsb


def hide_message_in_image(input_image_path: str | Path, message: bytes, output_image_path: str | Path) -> None:
    secret_image = lsb.hide(str(input_image_path), message.decode('latin1'))
    secret_image.save(str(output_image_path))


def reveal_message_from_image(image_path: str | Path) -> bytes:
    revealed_text = lsb.reveal(str(image_path))
    return revealed_text.encode('latin1')
