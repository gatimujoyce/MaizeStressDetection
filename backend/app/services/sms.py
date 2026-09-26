import os
import africastalking
from typing import Optional

# Initialize SDK
username = os.getenv("AFRICASTALKING_USERNAME", "sandbox")
api_key = os.getenv("AFRICASTALKING_API_KEY", "dummy_key")

africastalking.initialize(username, api_key)
sms = africastalking.SMS

def send_sms(phone_number: str, message: str) -> Optional[dict]:
    """
    Sends an SMS using Africa's Talking API.
    """
    try:
        response = sms.send(message, [phone_number])
        return response
    except Exception as e:
        print(f"Failed to send SMS to {phone_number}: {str(e)}")
        return None
