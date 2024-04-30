from http import HTTPStatus

import httpx
import pytest

from tests.functional.settings import Settings

Settings = Settings()


@pytest.mark.parametrize(
    'query_data, expected_answer',
    [
        (
                {'email': 'admin@test.com', 'password': 'admin'},
                {'status': HTTPStatus.OK}
        ),
        (
                {'email': 'admin@test.ru', 'password': 'test@test.ru'},
                {'status': HTTPStatus.FORBIDDEN}
        )

    ]
)
@pytest.mark.asyncio
async def test_login(
    query_data: dict,
    expected_answer: dict
):
    async with httpx.AsyncClient() as client:
        resp = await client.post(f'{Settings.service_url}/api/v1/user/login/', json=query_data)
        assert resp.status_code == expected_answer['status']
