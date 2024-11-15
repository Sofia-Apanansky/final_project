import hashlib
from Crypto import Random
from Crypto.Cipher import AES


class AESCipher:
    key: bytes
    block_size: int

    def __init__(self, aes_key: bytes) -> None:
        self.key = hashlib.sha256(aes_key).digest()  # Hashing the key
        self.block_size = AES.block_size

    def encrypt(self, plain_text: str) -> bytes:
        iv = self.__generate_iv()
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        plain_text = self.__pad(plain_text)
        encrypted_text = cipher.encrypt(plain_text.encode('utf-8'))
        return iv + encrypted_text

    def decrypt(self, encrypted_text: bytes) -> str:
        iv, encrypted_text = self.__split_iv_and_encrypted_text(encrypted_text)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)

        plain_text = cipher.decrypt(encrypted_text).decode('utf-8')
        return self.__unpad(plain_text)

    def __generate_iv(self) -> bytes:
        return Random.new().read(self.block_size)

    def __split_iv_and_encrypted_text(self, encrypted_text: bytes) -> tuple[bytes, bytes]:
        iv = encrypted_text[:self.block_size]
        encrypted_text_only = encrypted_text[self.block_size:]
        return iv, encrypted_text_only

    def __pad(self, plain_text: str) -> str:
        number_of_bytes_to_pad = self.block_size - len(plain_text) % self.block_size
        ascii_string = chr(number_of_bytes_to_pad)
        padding_str = number_of_bytes_to_pad * ascii_string
        padded_plain_text = plain_text + padding_str
        return padded_plain_text

    @staticmethod
    def __unpad(plain_text: str) -> str:
        last_character = plain_text[-1]
        number_of_bytes_to_remove = ord(last_character)
        return plain_text[:-number_of_bytes_to_remove]
