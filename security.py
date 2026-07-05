"""
Encryption layer for the journal app: derives a key from a user password
and encrypts/decrypts journal text with Fernet (AES-128 + HMAC).
"""
from __future__ import annotations

import base64
import os

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

_PBKDF2_ITERATIONS = 480_000
_SALT_SIZE = 16


class WrongPasswordError(Exception):
    """Raised when decryption fails, most likely due to a wrong password."""


def generate_salt() -> bytes:
    return os.urandom(_SALT_SIZE)


def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=_PBKDF2_ITERATIONS,
    )
    key_bytes = kdf.derive(password.encode("utf-8"))
    return base64.urlsafe_b64encode(key_bytes)


class JournalCipher:
    def __init__(self, password: str, salt: bytes):
        self._fernet = Fernet(derive_key(password, salt))

    def encrypt(self, plaintext: str) -> str:
        token = self._fernet.encrypt(plaintext.encode("utf-8"))
        return token.decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        try:
            return self._fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            raise WrongPasswordError("Could not decrypt - wrong password or corrupted data.") from exc


def save_salt(salt: bytes, path: str = "salt.bin") -> None:
    with open(path, "wb") as f:
        f.write(salt)


def load_salt(path: str = "salt.bin") -> bytes:
    with open(path, "rb") as f:
        return f.read()


def get_or_create_salt(path: str = "salt.bin") -> bytes:
    if os.path.exists(path):
        return load_salt(path)
    salt = generate_salt()
    save_salt(salt, path)
    return salt