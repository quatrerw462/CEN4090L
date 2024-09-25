
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import Padding


class AESCipher(object):
    def __init__(self, key,iv):
        self.key = key
        self.iv = iv

    def encrypt(self, plaintext):
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(self.iv))
        encryptor = cipher.encryptor()

        plaintext = Padding.appendPadding(plaintext, blocksize=Padding.AES_blocksize, mode='CBC')
        raw = bytes(plaintext, 'utf-8')

        encoded = encryptor.update(raw) + encryptor.finalize()
        return encoded

    def decrypt(self, raw):
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(self.iv))
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(raw) + decryptor.finalize()
        decrypted = str(decrypted, 'utf-8')
        decrypted = Padding.removePadding(decrypted, mode='ECB')

        return decrypted

