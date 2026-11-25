"""Cryptographically secure token generation, SHA-256 hashing, and authenticated encryption."""
import base64
import hashlib
import hmac
import secrets

from django.conf import settings


def generate_secure_token(nbytes: int = 32) -> str:
    """Generate a URL-safe cryptographically secure random token (256-bit default)."""
    return secrets.token_urlsafe(nbytes)


def hash_token(raw_token: str) -> str:
    """Compute SHA-256 hex digest for secure database lookup (never store raw tokens)."""
    return hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()


def _derive_keys() -> tuple[bytes, bytes]:
    secret = settings.SECRET_KEY.encode("utf-8")
    enc_key = hashlib.sha256(b"havells-sambandh-token-enc:" + secret).digest()
    mac_key = hashlib.sha256(b"havells-sambandh-token-mac:" + secret).digest()
    return enc_key, mac_key


def _keystream(enc_key: bytes, nonce: bytes, length: int) -> bytes:
    blocks = []
    counter = 0
    while sum(len(b) for b in blocks) < length:
        blocks.append(hashlib.sha256(enc_key + nonce + counter.to_bytes(4, "big")).digest())
        counter += 1
    return b"".join(blocks)[:length]


def encrypt_token(raw_token: str) -> str:
    """Authenticated encryption (Encrypt-then-MAC) so raw tokens are never stored in plain text."""
    enc_key, mac_key = _derive_keys()
    nonce = secrets.token_bytes(16)
    plaintext = raw_token.encode("utf-8")
    stream = _keystream(enc_key, nonce, len(plaintext))
    ciphertext = bytes(a ^ b for a, b in zip(plaintext, stream))
    tag = hmac.new(mac_key, nonce + ciphertext, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(nonce + tag + ciphertext).decode("ascii")


def decrypt_token(encrypted_value: str) -> str:
    """Verify MAC and decrypt an encrypted confirmation token."""
    if not encrypted_value:
        raise ValueError("Encrypted token is empty.")
    raw = base64.urlsafe_b64decode(encrypted_value.encode("ascii"))
    if len(raw) <= 48:
        raise ValueError("Invalid encrypted token payload.")
    nonce, tag, ciphertext = raw[:16], raw[16:48], raw[48:]
    enc_key, mac_key = _derive_keys()
    expected_tag = hmac.new(mac_key, nonce + ciphertext, hashlib.sha256).digest()
    if not hmac.compare_digest(tag, expected_tag):
        raise ValueError("Token integrity check failed.")
    stream = _keystream(enc_key, nonce, len(ciphertext))
    plaintext = bytes(a ^ b for a, b in zip(ciphertext, stream))
    return plaintext.decode("utf-8")
