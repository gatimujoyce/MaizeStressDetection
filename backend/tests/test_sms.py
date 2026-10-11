import pytest
from unittest.mock import patch, MagicMock
from app.services.sms import send_sms

def test_send_sms_success():
    mock_response = {
        "SMSMessageData": {
            "Message": "Sent to 1/1 Total Cost: KES 0.8000",
            "Recipients": [
                {
                    "statusCode": 101,
                    "number": "+254712345678",
                    "cost": "KES 0.8000",
                    "status": "Success",
                    "messageId": "ATXid_12345"
                }
            ]
        }
    }
    with patch("app.services.sms.sms.send", return_value=mock_response) as mock_send:
        result = send_sms("+254712345678", "Test message")
        assert result is True
        mock_send.assert_called_once_with("Test message", ["+254712345678"])

def test_send_sms_invalid_phone_number():
    mock_response = {
        "SMSMessageData": {
            "Message": "Sent to 0/1 Total Cost: KES 0",
            "Recipients": [
                {
                    "statusCode": 403,
                    "number": "+254712345678",
                    "cost": "0",
                    "status": "InvalidPhoneNumber",
                    "messageId": "None"
                }
            ]
        }
    }
    with patch("app.services.sms.sms.send", return_value=mock_response):
        result = send_sms("+254712345678", "Test message")
        assert result is False

def test_send_sms_empty_recipients():
    mock_response = {
        "SMSMessageData": {
            "Message": "No recipients",
            "Recipients": []
        }
    }
    with patch("app.services.sms.sms.send", return_value=mock_response):
        result = send_sms("+254712345678", "Test message")
        assert result is False

def test_send_sms_missing_keys_or_malformed():
    with patch("app.services.sms.sms.send", return_value={}):
        assert send_sms("+254712345678", "Test message") is False

    with patch("app.services.sms.sms.send", return_value="string response"):
        assert send_sms("+254712345678", "Test message") is False

    with patch("app.services.sms.sms.send", return_value={"SMSMessageData": {}}):
        assert send_sms("+254712345678", "Test message") is False

    with patch("app.services.sms.sms.send", return_value={"SMSMessageData": {"Recipients": [{}]}}):
        assert send_sms("+254712345678", "Test message") is False

def test_send_sms_exception_never_raises():
    with patch("app.services.sms.sms.send", side_effect=Exception("Connection refused")):
        result = send_sms("+254712345678", "Test message")
        assert result is False
