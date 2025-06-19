import pytest
from unittest.mock import patch, AsyncMock
from src.services.email import send_email, send_password_reset_email


@pytest.mark.asyncio
@patch("src.services.email.FastMail.send_message", new_callable=AsyncMock)
@patch("src.services.email.create_email_token")
async def test_send_email_success(mock_create_token, mock_send_message):
    mock_create_token.return_value = "mocked_token"

    await send_email(
        email="test@example.com", username="testuser", host="http://testhost"
    )

    mock_create_token.assert_called_once_with({"sub": "test@example.com"})
    mock_send_message.assert_awaited_once()


@pytest.mark.asyncio
@patch("src.services.email.FastMail.send_message", new_callable=AsyncMock)
@patch("src.services.email.create_email_token")
async def test_send_email_connection_error(mock_create_token, mock_send_message):
    mock_create_token.return_value = "mocked_token"
    mock_send_message.side_effect = Exception("Connection error")

    with pytest.raises(Exception) as exc:
        await send_email(
            email="test@example.com", username="testuser", host="http://testhost"
        )

    mock_create_token.assert_called_once_with({"sub": "test@example.com"})
    mock_send_message.assert_awaited_once()
    assert exc.type is not None


@pytest.mark.asyncio
@patch("src.services.email.FastMail.send_message", new_callable=AsyncMock)
async def test_send_password_reset_email_connection_error(mock_send_message):
    mock_send_message.side_effect = Exception("Connection error")

    with pytest.raises(Exception) as exc:
        await send_password_reset_email(
            email="test@example.com", token="reset_token", host="http://testhost"
        )

    mock_send_message.assert_awaited_once()
    assert exc.type is not None
