from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    rabbit_key_prefix: str = 'user-reporting.v1.'
    rabbit_username: str = 'praktikum'
    rabbit_password: str = 'praktikum'
    rabbit_heartbeat: int = 60
    rabbit_timeout: int = 300
    rabbit_host: str = 'rabbitmq'
    rabbit_exchange: str = 'notify-exchange'
    rabbit_exchange_type: str = 'topic'
    log_level: str = 'INFO'
    psql_dsn: PostgresDsn = Field(
            'postgresql+asyncpg://praktikum:praktikum@psql-server:5432/praktikum_database', alias='DB_DSN'
        )

settings = Settings()