# DH_Endpoint implements one side of the Diffie-Hellman key exchange protocol.
# It can generate a public key and compute the shared secret key using the peer's public key.
class DH_Endpoint(object):

    # Constructor: Initializes the prime modulus (p), base (g), and private key
    def __init__(self, p: int, g: int, private_key: int):
        # Prime number used as modulus in key exchange
        self.p = p
        # Base used for exponentiation
        self.g = g
        # The private secret key chosen by this endpoint
        self.private_key = private_key
        # This will hold the final shared full key after exchange
        self.full_key = None

    # Generates and returns the public key to be shared with the other party
    def generate_public_key(self):
        # Compute (g ^ private_key) mod p
        partial_key = self.g ** self.private_key
        partial_key = partial_key % self.p
        return partial_key

    # Given the other party's public key, compute the full shared key
    def generate_full_key(self, partial_key_r):
        # Compute (partial_key_r ^ private_key) mod p
        full_key = partial_key_r ** self.private_key
        full_key = full_key % self.p
        # Store the full shared key
        self.full_key = full_key
        return full_key
