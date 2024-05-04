from http import HTTPStatus

import httpx
import pytest

from tests.functional.settings import Settings

Settings = Settings()


@pytest.mark.parametrize(
    'query_data, expected_answer',
    [
        (
                {'version': 1, 'name': 'mail', 'text': '''
                Hiya {{ username }}!
            
                You did the right choice by joining our cinema club!
                We gonna send you some updates and news every second friday.
                So stay tuned!
            
                See you!
                Cinema Club'''},
                {'status': HTTPStatus.CREATED}
        ),
        (
                {'version': 1, 'name': 'mail', 'text': '''
                        Hiya {{ username }}!

                        You did the right choice by joining our cinema club!
                        We gonna send you some updates and news every second friday.
                        So stay tuned!

                        See you!
                        Cinema Club'''},
                {'status': HTTPStatus.INTERNAL_SERVER_ERROR}
        ),

    ]
)
@pytest.mark.asyncio
async def test_template_add(
    query_data: dict,
    expected_answer: dict
):
    async with httpx.AsyncClient() as client:
        resp = await client.post(f'{Settings.service_url}/api/v1/templates/', json=query_data)
        assert resp.status_code == expected_answer['status']
