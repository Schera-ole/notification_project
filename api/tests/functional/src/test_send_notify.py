from http import HTTPStatus

import httpx
import pytest
import datetime

from tests.functional.settings import Settings

Settings = Settings()


@pytest.mark.parametrize(
    'query_data, expected_answer',
    [
        (
                {'user_ids': ['1sad', '123asd'], 'template_name': 'mail', 'send_immediately': True,
                 'send_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                 'variables': {'asd': 'text'}
                 },
                {'type': str}
        ),
        (
                {'user_ids': ['testads', '123asd'], 'template_name': 'mail', 'send_immediately': True,
                 'send_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                 'variables': {'asd': 'text'}
                 },
                {'type': str}
        ),

    ]
)
@pytest.mark.asyncio
async def test_reg(
    query_data: dict,
    expected_answer: dict,
):
    async with httpx.AsyncClient() as client:
        resp = await client.post(f'{Settings.service_url}/api/v1/notification/send/', json=query_data)
        assert type(resp['notification_id']) == expected_answer['type']
