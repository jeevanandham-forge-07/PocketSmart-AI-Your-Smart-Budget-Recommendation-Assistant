import re
from typing import Tuple


def validate_email_str(email: str) -> bool:
    """Validate email address format"""
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email.strip()))


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """Check password strength constraints"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    if len(password) > 128:
        return False, "Password must not exceed 128 characters."
    return True, ""


def validate_budget_value(budget: float) -> Tuple[bool, str]:
    """Validate numeric budget values"""
    try:
        val = float(budget)
        if val <= 0:
            return False, "Budget must be greater than zero."
        if val > 100_000_000:
            return False, "Budget exceeds maximum limit of 10 Crores (100,000,000)."
        return True, ""
    except (ValueError, TypeError):
        return False, "Invalid numeric budget."
