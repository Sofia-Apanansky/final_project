from stegano import lsb


def hide_message_in_image(input_image_path: str, message: str, output_image_path: str) -> None:
    secret_image = lsb.hide(input_image_path, message)
    secret_image.save(output_image_path)


def reveal_message_from_image(image_path: str) -> str:
    revealed_text = lsb.reveal(image_path)
    return revealed_text
