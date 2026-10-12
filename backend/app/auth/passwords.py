import secrets
import string

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2, hash_len=32, salt_len=16)


def hash_password(plain_password: str) -> str:
    return _hasher.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, plain_password)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def generate_temporary_password(length: int = 14) -> str:
    """Cryptographically random temp password, guaranteed to contain
    upper/lower/digit/symbol so it satisfies strength requirements."""
    alphabet_groups = [
        string.ascii_lowercase,
        string.ascii_uppercase,
        string.digits,
        "!@#$%&*?",
    ]
    password_chars = [secrets.choice(group) for group in alphabet_groups]
    remaining_alphabet = "".join(alphabet_groups)
    password_chars += [secrets.choice(remaining_alphabet) for _ in range(length - len(password_chars))]
    secrets.SystemRandom().shuffle(password_chars)
    return "".join(password_chars)


def generate_username(name: str, existing_check) -> str:
    """existing_check(username) -> bool, True if taken. Appends a random
    suffix until a free username is found."""
    base = "".join(c for c in name.lower().replace(" ", ".") if c.isalnum() or c == ".")
    base = base or "user"
    candidate = base
    while existing_check(candidate):
        candidate = f"{base}{secrets.randbelow(9000) + 1000}"
    return candidate


def validate_password_strength(password: str) -> tuple[bool, str]:
    if len(password) < 10:
        return False, "Password must be at least 10 characters long."
    if not any(c.isupper() for c in password):
        return False, "Password must contain an uppercase letter."
    if not any(c.islower() for c in password):
        return False, "Password must contain a lowercase letter."
    if not any(c.isdigit() for c in password):
        return False, "Password must contain a digit."
    return True, ""
