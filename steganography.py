from pathlib import Path

from stegano import lsb

# Hide a byte message inside an image using LSB steganography
def hide_message_in_image(input_image_path: str | Path, message: bytes, output_image_path: str | Path) -> None:
    # The stegano library expects a string message, so decode bytes with 'latin1' to preserve byte values
    secret_image = lsb.hide(str(input_image_path), message.decode('latin1'))
    # Save the resulting image containing the hidden message
    secret_image.save(str(output_image_path))

# Reveal and extract the hidden byte message from a steganographic image
def reveal_message_from_image(image_path: str | Path) -> bytes:
    # Extract the hidden string message from the image
    revealed_text = lsb.reveal(str(image_path))
    # Encode the revealed string back to bytes using 'latin1' to preserve original byte values
    return revealed_text.encode('latin1')
