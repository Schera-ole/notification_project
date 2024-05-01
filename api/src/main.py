import http
import logging
from uuid import UUID
import uvicorn
from db.psql import get_session
from schema import Event, Template_schema
from model import Template
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
import pika
from fastapi import FastAPI, HTTPException, Depends
from pydantic.main import BaseModel
from db import psql
from config import settings
from sqlalchemy.orm import sessionmaker



logger = logging.getLogger(__name__)
logger.setLevel(settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global connection
    global channel

    engine = create_async_engine(str(settings.psql_dsn), echo=True, future=True)
    psql.async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    credentials = pika.PlainCredentials(
        settings.rabbit_username,
        settings.rabbit_password,
    )
    parameters = pika.ConnectionParameters(
        settings.rabbit_host,
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300
    )

    def _connect():
        return pika.BlockingConnection(parameters=parameters)

    connection = _connect()
    channel = connection.channel()

    channel.exchange_declare(
        exchange=settings.rabbit_exchange,
        exchange_type=settings.rabbit_exchange_type,
        durable=True,
    )
    channel.queue_declare(queue=settings.rabbit_events_queue_name, durable=True)

    logger.info('Connected to queue.')
    yield
    await psql.async_session.close()
    logger.info('Closing queue connection.')
    connection.close()




app = FastAPI(lifespan=lifespan)

@app.post('/send_notification/', status_code=http.HTTPStatus.CREATED)
def put_notification_to_queue(data: Event):
    try:
        channel.basic_publish(
            exchange=settings.rabbit_exchange,
            routing_key=settings.rabbit_events_queue_name,
            body=data.json(),
        )
    except Exception as err:
        logger.error(f'ERROR - queue publishing error: {str(err)}')
        raise HTTPException(
            http.HTTPStatus.INTERNAL_SERVER_ERROR,
            detail='500: Internal server error. Please try later.',
        )

    return {'201': 'Created event'}


@app.post('/api/add_template/', status_code=http.HTTPStatus.CREATED)
async def add_template(data: Template_schema, db_session: AsyncSession = Depends(get_session)):
    try:
        await Template(data).add_template(db_session)
    except Exception as err:
        logger.error(f'ERROR - cant create template: {str(err)}')
        raise HTTPException(
            http.HTTPStatus.INTERNAL_SERVER_ERROR,
            detail='500: Internal server error. Please try later.',
        )
    return {'201': 'Template has been created'}


@app.get('/api/get_templates/', status_code=http.HTTPStatus.OK)
async def add_template(db_session: AsyncSession = Depends(get_session)):
    data = await Template.get_templates(db_session)

    return data


if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=9090,
    )
