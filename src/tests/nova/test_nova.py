"""Тестирование создания юзера."""

from http import HTTPStatus
import pytest
from faker import Faker
from django.conf import settings

from nova.utils import validate_request_data


fake = Faker()


@pytest.mark.asyncio
class TestValidateRequestData:
    """Test the validate_request_data function."""

    async def test_validate_request_data_success(self, data=fake.text(max_nb_chars=settings.MAX_DATA_LEN), name=fake.file_name(extension="txt")):
        """
        Test the success case of the validate_request_data function.
        """
        assert not await validate_request_data(data, name)

    @pytest.mark.parametrize(
        "data, name", [
            ("", fake.file_name(extension="txt")),
            (" \n\t\r", fake.file_name(extension="txt")),
            ("1234567890"*1001, fake.file_name(extension="txt")),
            (fake.text(max_nb_chars=settings.MAX_DATA_LEN), ""),
            (fake.text(max_nb_chars=settings.MAX_DATA_LEN), fake.file_name(extension="txttx")),
            (fake.text(max_nb_chars=settings.MAX_DATA_LEN), fake.file_name(extension="t")),
            (fake.text(max_nb_chars=settings.MAX_DATA_LEN), f"{"1234567890"*9}.txt"),
            (fake.text(max_nb_chars=settings.MAX_DATA_LEN), ".txt"),
            ]
    )
    async def test_validate_request_data_fail(self, data, name):
        """
        Test the fail case of the validate_request_data function.
        """
        result = await validate_request_data(data, name)
        assert result.status_code == HTTPStatus.BAD_REQUEST
