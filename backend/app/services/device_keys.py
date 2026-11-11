"""Device keys: the secret a plot's sensor box uses to post readings. Only a hash is stored."""
import hashlib
import secrets

PREFIX = "mk_"


def make_key():
    """Returns (key, display_prefix, hash). The key is shown to the admin once and never stored."""
    key = PREFIX + secrets.token_urlsafe(32)
    return key, key[:10], hash_key(key)


def hash_key(key: str) -> str:
    # The key is 256 bits of randomness, so a plain SHA-256 is enough (no password-style slow hash needed).
    return hashlib.sha256(key.encode("utf-8")).hexdigest()
