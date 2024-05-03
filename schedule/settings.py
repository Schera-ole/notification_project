from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    log_level: str = 'INFO'

settings = Settings()