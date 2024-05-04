import logging
from contextlib import asynccontextmanager
import pika
import uvicorn
from config import settings
from db import psql
from fastapi import FastAPI
from api.v1 import notification, templates
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


logger = logging.getLogger('uvicorn')
logger.setLevel(settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):

    engine = create_async_engine(str(settings.psql_dsn), echo=True, future=True)
    psql.async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    logger.info('Connected to queue.')
    yield
    await psql.async_session.close()
    logger.info('Closing queue connection.')


app = FastAPI(lifespan=lifespan)
app.include_router(notification.router, prefix='/api/v1/notification', tags=['send_notification'])
app.include_router(templates.router, prefix='/api/v1/templates', tags=['templates'])


if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=9090,
    )
