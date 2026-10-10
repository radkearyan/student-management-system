import re

def validate_email(email):
    """Simple regex email validator."""
    if not email:
        return False
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))

def validate_phone(phone):
    """Simple phone validator (digits, plus sign)."""
    if not phone:
        return False
    pattern = r'^\+?[\d\s-]{10,15}$'
    return bool(re.match(pattern, phone))
