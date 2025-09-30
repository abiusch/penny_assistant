def calculate_area(length, width):
    """Calculate the area of a rectangle."""
    if length <= 0 or width <= 0:
        return 0
    return length * width

def validate_email(email):
    """Basic email validation."""
    return '@' in email and '.' in email
