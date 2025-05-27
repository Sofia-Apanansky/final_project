import hashlib
from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad


class AESCipher:
    key: bytes
    block_size: int

    def __init__(self, aes_key: bytes) -> None:
        self.key = hashlib.sha256(aes_key).digest()  # Hashing the key
        self.block_size = AES.block_size

    def encrypt(self, plain_text: str) -> bytes:
        iv = self.__generate_iv()
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        encoded_text = plain_text.encode('utf-16')
        encoded_text = self.__pad(encoded_text)
        encrypted_text = cipher.encrypt(encoded_text)
        return iv + encrypted_text

    def decrypt(self, encrypted_text: bytes) -> str:
        iv, encrypted_text = self.__split_iv_and_encrypted_text(encrypted_text)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)

        plain_text = cipher.decrypt(encrypted_text)
        return self.__unpad(plain_text).decode('utf-16')

    def __generate_iv(self) -> bytes:
        return Random.new().read(self.block_size)

    def __split_iv_and_encrypted_text(self, encrypted_text: bytes) -> tuple[bytes, bytes]:
        iv = encrypted_text[:self.block_size]
        encrypted_text_only = encrypted_text[self.block_size:]
        return iv, encrypted_text_only

    def __pad(self, plain_text: bytes) -> bytes:
        number_of_bytes_to_pad = self.block_size - len(plain_text) % self.block_size
        ascii_string = chr(number_of_bytes_to_pad).encode()
        padding_str = number_of_bytes_to_pad * ascii_string
        padded_plain_text = plain_text + padding_str
        return padded_plain_text

    @staticmethod
    def __unpad(plain_text: bytes) -> bytes:
        last_character = plain_text[-1:].decode()
        number_of_bytes_to_remove = ord(last_character)
        return plain_text[:-number_of_bytes_to_remove]
