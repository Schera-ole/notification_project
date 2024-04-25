from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    es_host: str = Field('elastic', alias='ELASTIC_HOST')
    es_port: int = Field(9200, alias='ELASTIC_PORT')
    es_person_index: str = 'persons'
    es_genre_index: str = 'genres'
    es_film_index: str = 'movies'

    es_config_index_path: str = './tests/functional/indexes_config/'

    redis_host: str = Field('redis', alias='REDIS_HOST')
    redis_port: int = Field(6379, alias='REDIS_PORT')
    service_url: str = Field('http://127.0.0.1:9999', alias='AUTH_URL')

    model_config = SettingsConfigDict(
        env_file='tests/functional/.env',
        env_file_encoding='utf-8',
        populate_by_name=True,
        extra='ignore'
    )


test_settings = Settings()
