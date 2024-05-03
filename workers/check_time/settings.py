from logging import config as logging_config
import os

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    rabbit_host: str = Field('rabbitmq', alias='RABBIT_HOST')
    rabbit_user: str = Field('praktikum', alias='RABBIT_USER')
    rabbit_password: str = Field('praktikum', alias='RABBIT_PASSWORD')
    queue_in: str = Field('notification.check_time_to_send', alias='QUEUE_IN')
    queue_out: str = Field('notification.get_user_data', alias='QUEUE_OUT')
    exchange_out: str = Field('notify-exchange', alias='EXCHANGE_OUT')

    class Config:
        env_file = '.env'


settings = Settings()
