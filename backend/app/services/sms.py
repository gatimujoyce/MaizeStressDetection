"""Send an SMS through Africa's Talking. Never raises: returns an SmsResult that is true only when the first recipient reports
Success (101), and carries the reason when it is not, plus the provider's message id for the later delivery report.

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


class SmsResult:
    """True when the SMS service accepted the message. Accepted is not the same as delivered: the phone's delivery report
    arrives later (see routers/sms_reports.py)."""

    def __init__(self, ok, reason=None, message_id=None):
        self.ok, self.reason, self.message_id = ok, reason, message_id

    def __bool__(self):
        return bool(self.ok)

    def __repr__(self):
        return f"SmsResult(ok={self.ok!r}, reason={self.reason!r}, message_id={self.message_id!r})"


def _endpoint(username: str) -> str:
    host = "api.sandbox.africastalking.com" if username == "sandbox" else "api.africastalking.com"
    return f"https://{host}/version1/messaging"


def _tls12_context() -> ssl.SSLContext:
    context = ssl.create_default_context()
    context.maximum_version = ssl.TLSVersion.TLSv1_2
    return context


def send_sms(phone_number: str, message: str) -> SmsResult:
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
            return SmsResult(False, "The SMS service sent an unexpected reply")
        recipients = payload.get("SMSMessageData", {}).get("Recipients", [])
        if not recipients or not isinstance(recipients, list) or not isinstance(recipients[0], dict):
            note = payload.get("SMSMessageData", {}).get("Message") if isinstance(payload.get("SMSMessageData"), dict) else None
            return SmsResult(False, f"The SMS service did not accept the message{f' ({note})' if note else ''}")
        first = recipients[0]
        if first.get("status") == "Success" and first.get("statusCode") == 101:
            return SmsResult(True, None, first.get("messageId"))
        return SmsResult(False, f"The SMS service said: {first.get('status') or 'not accepted'}", first.get("messageId"))
    except urllib.error.HTTPError as e:
        print(f"Failed to send SMS to {phone_number}: {e}")
        if e.code in (401, 403):
            return SmsResult(False, f"The SMS service rejected the API key or username ({e.code})")
        return SmsResult(False, f"The SMS service returned an error ({e.code})")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        print(f"Failed to send SMS to {phone_number}: {e}")
        return SmsResult(False, "Could not reach the SMS service")
    except Exception as e:
        print(f"Failed to send SMS to {phone_number}: {str(e)}")
        return SmsResult(False, "The message could not be sent")
