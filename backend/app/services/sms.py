"""Send an SMS through Africa's Talking. Never raises: returns True only when the first recipient reports Success (101).

The secure connection uses Python's built-in client and is capped at TLS 1.2. On some networks and security tools the
newer TLS 1.3 handshake, and the requests library's own connection settings, fail with WRONG_VERSION_NUMBER while a
plain TLS 1.2 connection works. Africa's Talking supports TLS 1.2."""
import json
import os
import ssl
import urllib.error
import urllib.parse
import urllib.request

TIMEOUT_SECONDS = 10


def _endpoint(username: str) -> str:
    host = "api.sandbox.africastalking.com" if username == "sandbox" else "api.africastalking.com"
    return f"https://{host}/version1/messaging"


def _tls12_context() -> ssl.SSLContext:
    context = ssl.create_default_context()
    context.maximum_version = ssl.TLSVersion.TLSv1_2
    return context


def send_sms(phone_number: str, message: str) -> bool:
    try:
        username = os.getenv("AFRICASTALKING_USERNAME", "sandbox")
        api_key = os.getenv("AFRICASTALKING_API_KEY", "dummy_key")
        body = urllib.parse.urlencode({"username": username, "to": phone_number, "message": message}).encode()
        request = urllib.request.Request(
            _endpoint(username),
            data=body,
            headers={"apiKey": api_key, "Accept": "application/json",
                     "Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS, context=_tls12_context()) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if not isinstance(payload, dict):
            return False
        recipients = payload.get("SMSMessageData", {}).get("Recipients", [])
        if not recipients or not isinstance(recipients, list):
            return False
        first = recipients[0]
        if not isinstance(first, dict):
            return False
        return first.get("status") == "Success" and first.get("statusCode") == 101
    except Exception as e:
        print(f"Failed to send SMS to {phone_number}: {str(e)}")
        return False