from unittest.mock import MagicMock, patch

from utils.telegram_notifier import send_telegram_message


def test_send_telegram_message_success(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")

    mock_response = MagicMock()
    mock_response.json.return_value = {"ok": True}

    with patch("utils.telegram_notifier.requests.post", return_value=mock_response) as mock_post:
        result = send_telegram_message("test message")

    assert result is True
    mock_post.assert_called_once()


def test_send_telegram_message_missing_credentials(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    result = send_telegram_message("test message")

    assert result is False


def test_send_telegram_message_api_error(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")

    mock_response = MagicMock()
    mock_response.json.return_value = {"ok": False, "description": "Bad Request"}

    with patch("utils.telegram_notifier.requests.post", return_value=mock_response):
        result = send_telegram_message("test message")

    assert result is False
