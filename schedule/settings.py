from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    log_level: str = 'INFO'
    api_host: str = 'notify'
    api_port: int = 9090

settings = Settings()