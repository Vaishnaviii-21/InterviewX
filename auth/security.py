"""
Cryptographic security and input validation module for InterviewX.
Uses PBKDF2-HMAC-SHA256 with cryptographically secure random salts.
Requires zero external C dependencies, ensuring 100% deployment reliability.
"""

import hashlib
import secrets
import re
from typing import Tuple

# Security constants
HASH_ALGORITHM = "sha256"
ITERATIONS = 100_000
SALT_BYTES = 16

def hash_password(password: str) -> str:
    """
    Hashes a plaintext password using PBKDF2-HMAC-SHA256 with a unique random salt.
    Format returned: pbkdf2:sha256:<iterations>$<salt_hex>$<hash_hex>
    """
    if not password:
        raise ValueError("Password cannot be empty.")
    
    salt = secrets.token_bytes(SALT_BYTES)
    derived_key = hashlib.pbkdf2_hmac(
        HASH_ALGORITHM,
        password.encode("utf-8"),
        salt,
        ITERATIONS
    )
    return f"pbkdf2:{HASH_ALGORITHM}:{ITERATIONS}${salt.hex()}${derived_key.hex()}"

def verify_password(plain_password: str, stored_hash: str) -> bool:
    """
    Verifies a plaintext password against a stored PBKDF2 hash using constant-time comparison.
    """
    if not plain_password or not stored_hash:
        return False
    
    try:
        parts = stored_hash.split("$")
        if len(parts) != 3:
            return False
        
        algo_header, salt_hex, expected_hash_hex = parts
        # Parse algo and iterations
        header_parts = algo_header.split(":")
        if len(header_parts) != 3 or header_parts[0] != "pbkdf2":
            return False
        
        algo = header_parts[1]
        iterations = int(header_parts[2])
        salt = bytes.fromhex(salt_hex)

        computed_key = hashlib.pbkdf2_hmac(
            algo,
            plain_password.encode("utf-8"),
            salt,
            iterations
        )
        # Constant-time comparison prevents timing attacks
        return secrets.compare_digest(computed_key.hex(), expected_hash_hex)
    except Exception:
        return False

# ==================== INPUT VALIDATORS ====================

USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_]{3,30}$")
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

def validate_username(username: str) -> Tuple[bool, str]:
    """
    Validates username format and length.
    Allowed: alphanumeric and underscores, length 3 to 30.
    """
    if not username:
        return False, "Username is required."
    clean = username.strip()
    if len(clean) < 3:
        return False, "Username must be at least 3 characters long."
    if len(clean) > 30:
        return False, "Username cannot exceed 30 characters."
    if not USERNAME_REGEX.match(clean):
        return False, "Username can only contain letters, numbers, and underscores."
    return True, ""

def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validates standard email address syntax.
    """
    if not email:
        return False, "Email address is required."
    clean = email.strip()
    if len(clean) > 100:
        return False, "Email address is too long."
    if not EMAIL_REGEX.match(clean):
        return False, "Please enter a valid email address (e.g., student@college.edu)."
    return True, ""

def validate_password(password: str) -> Tuple[bool, str]:
    """
    Validates password strength according to modern OWASP/NIST guidelines.
    Minimum 8 characters, must not exceed 128 characters, and must not start or end with whitespace.
    """
    if not password:
        return False, "Password is required."
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if len(password) > 128:
        return False, "Password cannot exceed 128 characters."
    if password.strip() != password:
        return False, "Password cannot start or end with whitespace."
    return True, ""

def validate_full_name(name: str) -> Tuple[bool, str]:
    """
    Validates candidate's display name.
    """
    if not name or not name.strip():
        return False, "Full name is required."
    clean = name.strip()
    if len(clean) < 2:
        return False, "Name must be at least 2 characters long."
    if len(clean) > 80:
        return False, "Name cannot exceed 80 characters."
    return True, ""
