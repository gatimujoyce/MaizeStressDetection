"""send_sms: True only when the first recipient reports Success (101); never raises."""
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


def _recipients(status, code):
    return {"SMSMessageData": {"Recipients": [{"status": status, "statusCode": code}]}}


def test_send_sms_success():
    with patch("urllib.request.urlopen", return_value=_reply(_recipients("Success", 101))) as urlopen:
        assert sms.send_sms("+254700000000", "hello") is True
    request = urlopen.call_args[0][0]
    assert request.full_url.endswith("/version1/messaging")
    assert b"to=%2B254700000000" in request.data and b"message=hello" in request.data
    assert urlopen.call_args[1]["context"].maximum_version.name == "TLSv1_2"


def test_send_sms_invalid_phone_number():
    with patch("urllib.request.urlopen", return_value=_reply(_recipients("InvalidPhoneNumber", 403))):
        assert sms.send_sms("123", "hello") is False


def test_send_sms_empty_recipients():
    with patch("urllib.request.urlopen", return_value=_reply({"SMSMessageData": {"Recipients": []}})):
        assert sms.send_sms("+254700000000", "hello") is False


def test_send_sms_missing_keys_or_malformed():
    for payload in ({}, {"SMSMessageData": {}}, {"SMSMessageData": {"Recipients": "oops"}},
                    {"SMSMessageData": {"Recipients": ["oops"]}}, ["not", "a", "dict"]):
        with patch("urllib.request.urlopen", return_value=_reply(payload)):
            assert sms.send_sms("+254700000000", "hello") is False


def test_send_sms_exception_never_raises():
    with patch("urllib.request.urlopen", side_effect=RuntimeError("network down")):
        assert sms.send_sms("+254700000000", "hello") is False
    with patch("urllib.request.urlopen",
               side_effect=urllib.error.HTTPError("u", 401, "Unauthorized", {}, None)):
        assert sms.send_sms("+254700000000", "hello") is False