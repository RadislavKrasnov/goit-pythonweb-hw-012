import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO
from src.services.upload_file import UploadFileService

@pytest.mark.asyncio
@patch("cloudinary.uploader.upload")
@patch("cloudinary.CloudinaryImage.build_url")
def test_upload_file(mock_build_url, mock_upload):
    file_mock = MagicMock()
    file_mock.file = BytesIO(b"fake image data")

    mock_upload.return_value = {"version": "123456"}
    mock_build_url.return_value = "http://cloudinary.com/fake_image_url"

    service = UploadFileService("demo_cloud", "demo_key", "demo_secret")
    result_url = service.upload_file(file_mock, "testuser")

    mock_upload.assert_called_once_with(file_mock.file, public_id="RestApp/testuser", overwrite=True)
    mock_build_url.assert_called_once_with(width=250, height=250, crop="fill", version="123456")
    assert result_url == "http://cloudinary.com/fake_image_url"
