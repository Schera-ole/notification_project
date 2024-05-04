import logging

import schedule
import time
import requests

from settings import settings
from http import HTTPStatus

logger = logging.getLogger('uvicorn')
logger.setLevel(settings.log_level)


def get_template_from_api():
    url = f'http://{settings.api_host}:{settings.api_port}/api/get_templates/'
    response = requests.get(url)
    if response.status_code == HTTPStatus.OK:
        return response.json()
    else:
        logger.error(f"Failed to retrieve templates from API. Status code: {response.status_code}")
        return None


def get_user_ids():
    url = f'http://{settings.api_host}:{settings.api_port}/api/get_users/'
    response = requests.get(url)
    if response.status_code == HTTPStatus.OK:
        return response.json()
    else:
        logger.error(f"Failed to retrieve users from API. Status code: {response.status_code}")
        return []


def call_api():
    templates = get_template_from_api()
    users = get_user_ids()

    if templates and users:
        for template in templates:
            url = f'http://{settings.api_host}:{settings.api_port}/send_notification/'
            data = {
                "user_ids": users,
                "template_name": template["name"],
                "version": template["version"],
                "send_immediately": True,
                "variables": {"key1": "value1", "key2": "value2"}
            }
            response = requests.post(url, json=data)
            logger.info(response.json())
    else:
        logger.error("No templates or users retrieved from API. Skipping notification calls.")


schedule.every().monday.at("00:00").do(call_api)

# Цикл для выполнения расписания
while True:
    schedule.run_pending()
    time.sleep(1)  # Ждем 1 секунду перед повторной проверкой расписания
