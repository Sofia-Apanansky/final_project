from stegano import lsb


def hide_message_in_image(input_image_path: str, message: bytes, output_image_path: str) -> None:
    secret_image = lsb.hide(input_image_path, message.decode('latin1'))
    secret_image.save(output_image_path)


def reveal_message_from_image(image_path: str) -> bytes:
    revealed_text = lsb.reveal(image_path)
    return revealed_text.encode('latin1')
