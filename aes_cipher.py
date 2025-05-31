import hashlib

from Crypto import Random
from Crypto.Cipher import AES


# AESCipher class provides AES encryption and decryption using CBC mode.
# It uses SHA-256 to hash the input key.
class AESCipher:
    key: bytes
    block_size: int

    def __init__(self, aes_key: bytes) -> None:
        # Hash the given key using SHA-256 to ensure it is 32 bytes long
        self.key = hashlib.sha256(aes_key).digest()
        # AES block size is 16 bytes
        self.block_size = AES.block_size

    def encrypt(self, plain_text: str) -> bytes:
        # Generate a random IV (Initialization Vector)
        iv = self.__generate_iv()
        # Create AES cipher in CBC mode with the IV
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        # Encode the plain text as UTF-16 to preserve character integrity
        encoded_text = plain_text.encode('utf-16')
        # Pad the encoded text to match block size
        encoded_text = self.__pad(encoded_text)
        # Encrypt the padded text
        encrypted_text = cipher.encrypt(encoded_text)
        # Prepend IV to the ciphertext for use in decryption
        return iv + encrypted_text

    def decrypt(self, encrypted_text: bytes) -> str:
        # Split the IV and actual encrypted content
        iv, encrypted_text = self.__split_iv_and_encrypted_text(encrypted_text)
        # Create AES cipher in CBC mode with the extracted IV
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        # Decrypt the content
        plain_text = cipher.decrypt(encrypted_text)
        # Remove padding and decode the original text
        return self.__unpad(plain_text).decode('utf-16')

    def __generate_iv(self) -> bytes:
        # Securely generate a random IV of AES block size
        return Random.new().read(self.block_size)

    def __split_iv_and_encrypted_text(self, encrypted_text: bytes) -> tuple[bytes, bytes]:
        # Extract IV from the start of the ciphertext
        iv = encrypted_text[:self.block_size]
        # Extract the actual encrypted message after the IV
        encrypted_text_only = encrypted_text[self.block_size:]
        return iv, encrypted_text_only

    def __pad(self, plain_text: bytes) -> bytes:
        # Calculate the number of padding bytes needed
        number_of_bytes_to_pad = self.block_size - len(plain_text) % self.block_size
        # Create a padding byte
        ascii_string = chr(number_of_bytes_to_pad).encode()
        # Repeat the padding byte to reach required length
        padding_str = number_of_bytes_to_pad * ascii_string
        # Append padding to the plaintext
        padded_plain_text = plain_text + padding_str
        return padded_plain_text

    @staticmethod
    def __unpad(plain_text: bytes) -> bytes:
        # Get value of the last byte to determine padding length
        last_character = plain_text[-1:].decode()
        number_of_bytes_to_remove = ord(last_character)
        # Remove the padding bytes from the end
        return plain_text[:-number_of_bytes_to_remove]
