
import hashlib
from .constants import HASH_PREFIX

def hash_password(password: str) -> str:
    # Simple sha256 hash (saltless, per spec). For stronger security, add salt + PBKDF2/argon2.
    h = hashlib.sha256(password.encode('utf-8')).hexdigest()
    return f"{HASH_PREFIX}{h}"

def is_hashed(value: str) -> bool:
    return isinstance(value, str) and value.startswith(HASH_PREFIX)

def verify_password(stored: str, provided: str) -> bool:
    if not isinstance(stored, str):
        return False
    if is_hashed(stored):
        return hash_password(provided) == stored
    # Legacy plaintext support (will be migrated on save)
    return stored == provided
