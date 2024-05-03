from logging import config as logging_config
import os

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    rabbit_host: str = Field('rabbitmq', alias='RABBIT_HOST')
    rabbit_user: str = Field('praktikum', alias='RABBIT_USER')
    rabbit_password: str = Field('praktikum', alias='RABBIT_PASSWORD')
    queue_in: str = Field('notification.get_user_data', alias='QUEUE_IN')
    queue_out: str = Field('notification.send_to_user', alias='QUEUE_OUT')
    exchange_out: str = Field('send-exchange', alias='EXCHANGE_OUT')
    auth_url: str = 'http://auth:9999/auth/v1/user/get-user-info/'

    class Config:
        env_file = '.env'


settings = Settings()
