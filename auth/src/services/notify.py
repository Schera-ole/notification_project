from abc import abstractmethod, ABC
import json
import logging

import httpx

from core.settings import settings


class NotifyAbstract(ABC):

    @abstractmethod
    async def send_notify(self, *args, **kwargs):
        pass


class NotifyClient(NotifyAbstract):

    @staticmethod
    async def send_notify(user_id):
        data = {
            'user_ids': [str(user_id)],
            'template_name': settings.welcome_template_name,
            'version': settings.welcome_template_version,
            'send_immediately': True,
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f'{settings.notify_api_url}/send_notification/', json=data)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                logging.error(f'Problems with sending notification to user {user_id}: {exc}')
