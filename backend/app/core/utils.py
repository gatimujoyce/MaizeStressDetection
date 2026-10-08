import re
from fastapi import HTTPException, status

def normalize_ke_phone(raw: str) -> str:
    """
    Normalizes a Kenyan phone number to E.164 format: +254XXXXXXXXX.
    Strips spaces, dashes, brackets.
    Accepts: +2547..., +2541..., 2547..., 2541..., 07..., 01...
    Rejects others with a 422 HTTPException.
    """
    if not isinstance(raw, str):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Phone number must be a string."
        )

    # Strip spaces, dashes, brackets
    cleaned = re.sub(r'[\s\-\(\)]', '', raw)

    if cleaned.startswith('+254'):
        normalized = cleaned
    elif cleaned.startswith('254'):
        normalized = '+' + cleaned
    elif cleaned.startswith('0'):
        normalized = '+254' + cleaned[1:]
    else:
        # Invalid format
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid Kenyan phone number format. Use formats such as 07XXXXXXXX or +2547XXXXXXXX."
        )

    # Final check: ^\+254[17]\d{8}$
    if not re.match(r'^\+254[17]\d{8}$', normalized):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid Kenyan phone number format. Must be +254 followed by 7 or 1 and 8 digits."
        )

    return normalized
