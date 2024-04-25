from http import HTTPStatus

import httpx
import pytest

from tests.functional.settings import Settings

Settings = Settings()


@pytest.mark.parametrize(
    'query_data, expected_answer',
    [
        (
                {'email': 'asd@asd.ad', 'password': 'asd@asd.ad'},
                {'status': HTTPStatus.CREATED}
        ),
        (
                {'email': 'asd@asd.ad', 'password': 'asd@asd.ad'},
                {'status': HTTPStatus.BAD_REQUEST}
        )

    ]
)
@pytest.mark.asyncio
async def test_reg(
    query_data: dict,
    expected_answer: dict,
):
    async with httpx.AsyncClient() as client:
        resp = await client.post(f'{Settings.service_url}/api/v1/user/signup/', json=query_data)
        assert resp.status_code == expected_answer['status']
