from logging import config as logging_config

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

from core.logger import LOGGING

# Применяем настройки логирования
logging_config.dictConfig(LOGGING)


class Settings(BaseSettings):

    project_name: str = 'Praktikum Auth'

    redis_host: str = Field('redis', alias='REDIS_HOST')
    redis_port: int = Field(6379, alias='REDIS_PORT')

    psql_dsn: PostgresDsn = Field(
        'postgresql+asyncpg://praktikum:praktikum@psql-server:5432/praktikum_database', alias='DB_DSN'
    )

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        populate_by_name=True,
        extra='ignore'
    )

    secret_key: str = Field(alias='secret_key')

    expiry_access: int = 60 * 15  # в секундах - то есть 15 минут
    expiry_refresh: int = 60 * 60 * 2  # в секундах - то есть 2 часа
    jwt_algorithm: str = 'HS256'
    prefix_redis_token: str = 'yandex'
    prefix_logout_token: str = f'logout:{prefix_redis_token}'

    jaeger_exporter_host: str = Field('jaeger', alias='SERVICE_JAEGER_NAME')
    jaeger_exporter_port: int = Field(6831, alias='JAEGER_EXPORTER_PORT')
    service_jaeger_name: str = Field('auth', alias='SERVICE_JAEGER_NAME')
    is_enable_tracer: bool = Field(True, alias='IS_ENABLE_TRACER')

    # Notification API
    welcome_template_name: str = 'welcome'
    notify_api_url: str = Field('http://notify:9090', alias='NOTIFY_API_URL')


class YandexSettings(BaseSettings):
    YANDEX_CLIENT_ID: str = Field(alias='YANDEX_CLIENT_ID')
    YANDEX_CLIENT_SECRET: str = Field(alias='YANDEX_CLIENT_SECRET')
    YANDEX_REDIRECT_URI: str = Field(alias='YANDEX_REDIRECT_URI')

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
yandex_settings = YandexSettings()
