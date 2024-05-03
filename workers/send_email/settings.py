from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    rabbit_host: str = Field('rabbitmq', alias='RABBIT_HOST')
    rabbit_user: str = Field('praktikum', alias='RABBIT_USER')
    rabbit_password: str = Field('praktikum', alias='RABBIT_PASSWORD')
    queue_in: str = Field('notification.send_to_user', alias='QUEUE_IN')
    exchange_out: str = Field('finish-exchange', alias='EXCHANGE_OUT')

    psql_dsn: PostgresDsn = Field(
        'postgresql+psycopg2://praktikum:praktikum@psql-server:5432/praktikum', alias='DB_DSN'
    )

    sender: str = 'test@test.com'
    password: str = 'test'
    smtpStr: str = 'smtp.google.com'
    smtpPort: int = 587


    class Config:
        env_file = '.env'


settings = Settings()
