import pytest

from fairy.desktop.api_client import ApiResponseError, decode_chat_reply, decode_health


def test_decode_chat_reply_returns_trimmed_reply():
    assert decode_chat_reply(b'{"reply": "  Open the document.  "}') == "Open the document."


def test_decode_chat_reply_rejects_invalid_utf8():
    with pytest.raises(ApiResponseError):
        decode_chat_reply(b"\xff")


def test_decode_chat_reply_rejects_malformed_json():
    with pytest.raises(ApiResponseError):
        decode_chat_reply(b"not json")


def test_decode_chat_reply_rejects_missing_reply():
    with pytest.raises(ApiResponseError):
        decode_chat_reply(b'{"message": "missing"}')


def test_decode_chat_reply_rejects_empty_reply():
    with pytest.raises(ApiResponseError):
        decode_chat_reply(b'{"reply": "   "}')


def test_decode_health_requires_expected_identity():
    assert decode_health(b'{"service": "neurofairy", "status": "ok"}') is True
    assert decode_health(b'{"service": "something-else", "status": "ok"}') is False
