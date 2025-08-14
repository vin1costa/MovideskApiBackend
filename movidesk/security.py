# movidesk/security.py
import base64
import hashlib
import hmac
import secrets
from typing import Optional

_ALGO = "pbkdf2"
_ITER = 120_000
_SALT_LEN = 16

def is_hashed(s: Optional[str]) -> bool:
    return isinstance(s, str) and s.startswith(f"{_ALGO}$")

def hash_password(plain: Optional[str]) -> str:
    if plain is None:
        plain = ""
    salt = secrets.token_bytes(_SALT_LEN)
    dk = hashlib.pbkdf2_hmac("sha256", plain.encode("utf-8"), salt, _ITER)
    return f"{_ALGO}${_ITER}${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"

def verify_password(stored: Optional[str], provided: Optional[str]) -> bool:
    stored = stored or ""
    provided = provided or ""

    # 1ª execução / admin sem senha
    if stored == "" and provided == "":
        return True

    # Compatibilidade: senha antiga em texto puro
    if not is_hashed(stored):
        return hmac.compare_digest(stored, provided)

    # Hash PBKDF2
    try:
        _, iter_s, salt_b64, hash_b64 = stored.split("$")
        it = int(iter_s)
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
        test = hashlib.pbkdf2_hmac("sha256", provided.encode("utf-8"), salt, it)
        return hmac.compare_digest(test, expected)
    except Exception:
        return False
