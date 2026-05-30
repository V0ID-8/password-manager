import os
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet, InvalidToken

SALT_FILE = "salt.bin"
ITERATIONS = 480_000  # OWASP 2023 recommended minimum for PBKDF2-SHA256


def load_or_create_salt() -> bytes:
    if os.path.exists(SALT_FILE):
        with open(SALT_FILE, "rb") as f:
            return f.read()
    salt = os.urandom(32)
    with open(SALT_FILE, "wb") as f:
        f.write(salt)
    return salt


def derive_key(master_password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(master_password.encode("utf-8")))


def encrypt(data: bytes, key: bytes) -> bytes:
    return Fernet(key).encrypt(data)


def decrypt(token: bytes, key: bytes) -> bytes:
    # Raises InvalidToken if the key is wrong or ciphertext was tampered with.
    return Fernet(key).decrypt(token)


if __name__ == "__main__":
    print("Running crypto sanity checks...")

    salt = os.urandom(32)
    key = derive_key("correct-horse-battery", salt)
    wrong_key = derive_key("wrong-password", salt)

    plaintext = b"Hello, vault!"
    ciphertext = encrypt(plaintext, key)

    # Correct key round-trip
    recovered = decrypt(ciphertext, key)
    assert recovered == plaintext, "Round-trip failed"
    print("  [OK] encrypt -> decrypt round-trip")

    # Wrong key must raise InvalidToken
    try:
        decrypt(ciphertext, wrong_key)
        print("  [FAIL] Wrong key did not raise InvalidToken")
    except InvalidToken:
        print("  [OK] Wrong key correctly raises InvalidToken")

    # Tampered ciphertext must raise InvalidToken
    tampered = ciphertext[:-4] + b"XXXX"
    try:
        decrypt(tampered, key)
        print("  [FAIL] Tampered ciphertext did not raise InvalidToken")
    except (InvalidToken, Exception):
        print("  [OK] Tampered ciphertext correctly raises InvalidToken")

    print("All checks passed.")
