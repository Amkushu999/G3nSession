import re
from typing import Tuple

def validate_phone_number(phone_number: str) -> Tuple[bool, str]:
    """
    Validate and format a phone number.
    
    Args:
        phone_number: The phone number to validate
        
    Returns:
        Tuple containing:
        - Boolean indicating if the number is valid
        - The formatted number or error message
    """
    # Remove any non-digit characters except the + at the beginning
    cleaned_number = re.sub(r'[^\d+]', '', phone_number)
    
    # Check if the number starts with + and has at least 7 digits after
    if not cleaned_number.startswith('+'):
        return False, "Phone number must start with a '+' sign"
        
    # Remove the + and check if the rest are digits
    number_without_plus = cleaned_number[1:]
    if not number_without_plus.isdigit():
        return False, "Phone number must contain only digits after the '+' sign"
        
    # Check if it has a reasonable length (at least 7 digits, not more than 15)
    if len(number_without_plus) < 7 or len(number_without_plus) > 15:
        return False, "Phone number must be between 7 and 15 digits long"
        
    return True, cleaned_number

def format_verification_code(code: str) -> Tuple[bool, str]:
    """
    Format verification code by removing spaces and non-digits.
    
    Args:
        code: The verification code
        
    Returns:
        Tuple containing:
        - Boolean indicating if the code is valid
        - The formatted code or error message
    """
    # Remove spaces and non-digit characters
    cleaned_code = re.sub(r'[^\d]', '', code)
    
    # Most Telegram verification codes are 5 digits
    if len(cleaned_code) < 3 or len(cleaned_code) > 7:
        return False, "Verification code should be between 3 and 7 digits"
        
    return True, cleaned_code

def safe_str(value) -> str:
    """
    Safely convert a value to string, handling None values.
    
    Args:
        value: Value to convert to string
        
    Returns:
        String representation or 'Not set' if None
    """
    return str(value) if value is not None else 'Not set'
