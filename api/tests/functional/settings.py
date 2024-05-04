from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    es_config_index_path: str = './tests/functional/indexes_config/'

    service_url: str = Field('http://127.0.0.1:9090', alias='API_URL')

    model_config = SettingsConfigDict(
        env_file='tests/functional/.env',
        env_file_encoding='utf-8',
        populate_by_name=True,
        extra='ignore'
    )


test_settings = Settings()
