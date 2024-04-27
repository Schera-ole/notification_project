from abc import abstractmethod, ABC
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
            'user_ids': [user_id],
            'template_name': settings.welcome_template_name,
            'send_immediately': True,
        }
        # TODO добавить повторную отправку в случае недоступности апи
        async with httpx.AsyncClient() as client:
            try:
                response = client.post(f'{settings.notify_api_url}/send_notification/', json=data)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                logging.error(f'Problems with sending notification to user {user_id}: {exc}')
