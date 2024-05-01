from pydantic_settings import BaseSettings
from pydantic import Field, PostgresDsn


class Settings(BaseSettings):
    rabbit_events_queue_name: str = 'email'

    rabbit_username: str = 'praktikum'
    rabbit_password: str = 'praktikum'
    rabbit_host: str = 'rabbitmq'
    rabbit_exchange: str = 'notify-exchange'
    rabbit_exchange_type: str = 'direct'
    log_level: str = 'INFO'
    psql_dsn: PostgresDsn = Field(
            'postgresql+asyncpg://praktikum:praktikum@psql-server:5432/praktikum_database', alias='DB_DSN'
        )

settings = Settings()