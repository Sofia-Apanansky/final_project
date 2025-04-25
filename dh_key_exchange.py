class DH_Endpoint(object):
    def __init__(self, p: int, g: int, private_key: int):
        self.p = p
        self.g = g
        self.private_key = private_key
        self.full_key = None

    def generate_public_key(self):
        partial_key = self.g ** self.private_key
        partial_key = partial_key % self.p
        return partial_key

    def generate_full_key(self, partial_key_r):
        full_key = partial_key_r ** self.private_key
        full_key = full_key % self.p
        self.full_key = full_key
        return full_key
