import os
import africastalking
from typing import Optional

# Initialize SDK
username = os.getenv("AFRICASTALKING_USERNAME", "sandbox")
api_key = os.getenv("AFRICASTALKING_API_KEY", "dummy_key")

africastalking.initialize(username, api_key)
sms = africastalking.SMS

def send_sms(phone_number: str, message: str) -> bool:
    """
    Sends an SMS using Africa's Talking API.
    Returns True if recipient status is 'Success' (statusCode 101), False otherwise.
    Never raises exceptions.
    """
    try:
        response = sms.send(message, [phone_number])
        if not isinstance(response, dict):
            return False
        recipients = response.get("SMSMessageData", {}).get("Recipients", [])
        if not recipients or not isinstance(recipients, list):
            return False
        first_recipient = recipients[0]
        if not isinstance(first_recipient, dict):
            return False
        return (
            first_recipient.get("status") == "Success"
            and first_recipient.get("statusCode") == 101
        )
    except Exception as e:
        print(f"Failed to send SMS to {phone_number}: {str(e)}")
        return False

