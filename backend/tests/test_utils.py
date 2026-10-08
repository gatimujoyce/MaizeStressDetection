import pytest
from fastapi import HTTPException
from app.core.utils import normalize_ke_phone

def test_normalize_ke_phone_accepted_formats():
    expected = "+254712345678"
    formats = [
        "+254712345678",
        "+254 712 345 678",
        "+254-712-345-678",
        "(+254) 712345678",
        "254712345678",
        "0712345678"
    ]
    for fmt in formats:
        assert normalize_ke_phone(fmt) == expected

    expected_1 = "+254112345678"
    formats_1 = [
        "+254112345678",
        "254112345678",
        "0112345678"
    ]
    for fmt in formats_1:
        assert normalize_ke_phone(fmt) == expected_1

def test_normalize_ke_phone_rejections():
    invalid_cases = [
        "+254812345678", # start with 8 not 7 or 1
        "+255712345678", # wrong country code
        "071234567",     # too short
        "+2547123456789", # too long
        "0712abc456",    # letters
        "invalid_str",   # generic string
        ""               # empty
    ]
    for case in invalid_cases:
        with pytest.raises(HTTPException) as exc:
            normalize_ke_phone(case)
        assert exc.value.status_code == 422
