"""
Minimal validators for testing purposes.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def validate_audio_file(file_path: str, max_size_mb: int = 100) -> Tuple[bool, str]:
    """
    Validate an audio file.

    Args:
        file_path: Path to the audio file
        max_size_mb: Maximum file size in MB

    Returns:
        Tuple of (is_valid, error_message)
    """
    path = Path(file_path)

    # Check if file exists
    if not path.exists():
        return False, f"File not found: {file_path}"

    # Check file size
    max_size_bytes = max_size_mb * 1024 * 1024
    file_size = path.stat().st_size

    if file_size > max_size_bytes:
        return False, f"File too large: {file_size} bytes (max: {max_size_bytes} bytes)"

    # Check file extension
    valid_extensions = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac"}
    if path.suffix.lower() not in valid_extensions:
        return (
            False,
            f"Invalid file extension: {path.suffix}. Valid extensions: {', '.join(valid_extensions)}",
        )

    # Check if file is readable
    try:
        with open(file_path, "rb") as f:
            f.read(1024)  # Read first 1KB to check readability
    except (IOError, OSError) as e:
        return False, f"Cannot read file: {e}"

    return True, ""


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email or not isinstance(email, str):
        return False, "Email must be a non-empty string"

    # Basic email validation
    if "@" not in email:
        return False, "Email must contain '@' symbol"

    parts = email.split("@")
    if len(parts) != 2:
        return False, "Invalid email format"

    local_part, domain = parts

    if not local_part or not domain:
        return False, "Email must have both local part and domain"

    if "." not in domain:
        return False, "Domain must contain '.'"

    # Check for common issues
    if ".." in email:
        return False, "Email cannot contain consecutive dots"

    if email.startswith(".") or email.endswith("."):
        return False, "Email cannot start or end with a dot"

    return True, ""


def validate_username(username: str) -> Tuple[bool, str]:
    """
    Validate username.

    Args:
        username: Username to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not username or not isinstance(username, str):
        return False, "Username must be a non-empty string"

    # Length check
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"

    if len(username) > 50:
        return False, "Username must be at most 50 characters long"

    # Character check
    import re

    if not re.match(r"^[a-zA-Z0-9_.-]+$", username):
        return (
            False,
            "Username can only contain letters, numbers, dots, hyphens, and underscores",
        )

    # Reserved names check
    reserved_names = {"admin", "root", "system", "support", "help", "info"}
    if username.lower() in reserved_names:
        return False, "This username is reserved"

    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    """
    Validate password strength.

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not password or not isinstance(password, str):
        return False, "Password must be a non-empty string"

    # Length check
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    # Complexity check
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)

    errors = []
    if not has_upper:
        errors.append("at least one uppercase letter")
    if not has_lower:
        errors.append("at least one lowercase letter")
    if not has_digit:
        errors.append("at least one digit")

    if errors:
        return False, f"Password must contain: {', '.join(errors)}"

    # Common password check (simplified)
    common_passwords = {"password", "12345678", "qwerty", "admin", "letmein"}
    if password.lower() in common_passwords:
        return False, "Password is too common"

    return True, ""


def validate_file_extension(
    filename: str, allowed_extensions: List[str]
) -> Tuple[bool, str]:
    """
    Validate file extension.

    Args:
        filename: Name of the file
        allowed_extensions: List of allowed extensions (with or without dot)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not filename:
        return False, "Filename cannot be empty"

    # Normalize extensions
    normalized_extensions = []
    for ext in allowed_extensions:
        if not ext.startswith("."):
            ext = "." + ext
        normalized_extensions.append(ext.lower())

    # Get file extension
    path = Path(filename)
    file_ext = path.suffix.lower()

    if not file_ext:
        return (
            False,
            f"File must have an extension. Allowed: {', '.join(normalized_extensions)}",
        )

    if file_ext not in normalized_extensions:
        return (
            False,
            f"Invalid file extension: {file_ext}. Allowed: {', '.join(normalized_extensions)}",
        )

    return True, ""


def validate_integer(
    value: any, min_value: Optional[int] = None, max_value: Optional[int] = None
) -> Tuple[bool, str]:
    """
    Validate integer value.

    Args:
        value: Value to validate
        min_value: Minimum allowed value
        max_value: Maximum allowed value

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        int_value = int(value)
    except (ValueError, TypeError):
        return False, "Value must be an integer"

    if min_value is not None and int_value < min_value:
        return False, f"Value must be at least {min_value}"

    if max_value is not None and int_value > max_value:
        return False, f"Value must be at most {max_value}"

    return True, ""


def validate_float(
    value: any, min_value: Optional[float] = None, max_value: Optional[float] = None
) -> Tuple[bool, str]:
    """
    Validate float value.

    Args:
        value: Value to validate
        min_value: Minimum allowed value
        max_value: Maximum allowed value

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        float_value = float(value)
    except (ValueError, TypeError):
        return False, "Value must be a number"

    if min_value is not None and float_value < min_value:
        return False, f"Value must be at least {min_value}"

    if max_value is not None and float_value > max_value:
        return False, f"Value must be at most {max_value}"

    return True, ""


def validate_string(
    value: any, min_length: Optional[int] = None, max_length: Optional[int] = None
) -> Tuple[bool, str]:
    """
    Validate string value.

    Args:
        value: Value to validate
        min_length: Minimum allowed length
        max_length: Maximum allowed length

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(value, str):
        return False, "Value must be a string"

    if min_length is not None and len(value) < min_length:
        return False, f"String must be at least {min_length} characters long"

    if max_length is not None and len(value) > max_length:
        return False, f"String must be at most {max_length} characters long"

    return True, ""
