"""send_sms: the result is true only when the first recipient reports Success (101); it never raises, and a refusal carries a reason."""
import io
import json
import urllib.error
from unittest.mock import patch

from app.services import sms


class _Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _reply(payload):
    return _Response(json.dumps(payload).encode("utf-8"))


def _recipients(status, code, message_id=None):
    recipient = {"status": status, "statusCode": code}
    if message_id:
        recipient["messageId"] = message_id
    return {"SMSMessageData": {"Recipients": [recipient]}}


def test_send_sms_success():
    with patch("urllib.request.urlopen", return_value=_reply(_recipients("Success", 101, "ATXid_1"))) as urlopen:
        result = sms.send_sms("+254700000000", "hello")
    assert result and result.ok is True
    assert result.message_id == "ATXid_1" and result.reason is None
    request = urlopen.call_args[0][0]
    assert request.full_url.endswith("/version1/messaging")
    assert b"to=%2B254700000000" in request.data and b"message=hello" in request.data
    assert urlopen.call_args[1]["context"].maximum_version.name == "TLSv1_2"


def test_send_sms_invalid_phone_number():
    with patch("urllib.request.urlopen", return_value=_reply(_recipients("InvalidPhoneNumber", 403))):
        result = sms.send_sms("123", "hello")
    assert not result and "InvalidPhoneNumber" in result.reason


def test_send_sms_empty_recipients():
    with patch("urllib.request.urlopen", return_value=_reply({"SMSMessageData": {"Recipients": []}})):
        result = sms.send_sms("+254700000000", "hello")
    assert not result and result.reason


def test_send_sms_missing_keys_or_malformed():
    for payload in ({}, {"SMSMessageData": {}}, {"SMSMessageData": {"Recipients": "oops"}},
                    {"SMSMessageData": {"Recipients": ["oops"]}}, ["not", "a", "dict"]):
        with patch("urllib.request.urlopen", return_value=_reply(payload)):
            assert not sms.send_sms("+254700000000", "hello")


def test_send_sms_exception_never_raises():
    with patch("urllib.request.urlopen", side_effect=RuntimeError("network down")):
        result = sms.send_sms("+254700000000", "hello")
    assert not result and result.reason
    with patch("urllib.request.urlopen",
               side_effect=urllib.error.HTTPError("u", 401, "Unauthorized", {}, None)):
        result = sms.send_sms("+254700000000", "hello")
    assert not result and "401" in result.reason
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("no route")):
        result = sms.send_sms("+254700000000", "hello")
    assert not result and result.reason == "Could not reach the SMS service"