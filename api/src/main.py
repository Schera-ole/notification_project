import http
import json
import logging
from contextlib import asynccontextmanager
import uuid

import pika
import uvicorn
from config import settings
from db import psql
from db.psql import get_session
from fastapi import Depends, FastAPI, HTTPException
from model import Template
from schema import Event, Template_schema
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger('uvicorn')
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
        heartbeat=settings.rabbit_heartbeat,
        blocked_connection_timeout=settings.rabbit_timeout,
    )

    def _connect():
        return pika.BlockingConnection(parameters=parameters)

    connection = _connect()
    channel = connection.channel()
    logger.info('Connected to queue.')
    yield
    await psql.async_session.close()
    logger.info('Closing queue connection.')
    connection.close()


app = FastAPI(lifespan=lifespan)


@app.post('/send_notification/', status_code=http.HTTPStatus.CREATED, response_model=dict)
def put_notification_to_queue(data: Event):
    data_dump = data.model_dump()
    if data_dump['send_immediately']:
        routing_key = f'{settings.rabbit_key_prefix}register'
        
    else:
        routing_key = f'{settings.rabbit_key_prefix}time'
    headers={'routing_key': routing_key}
    notification_id = uuid.uuid4()
    data_dump['notification_id'] = str(notification_id)
    try:
        channel.basic_publish(
            exchange=settings.rabbit_exchange,
            routing_key=routing_key,
            body=json.dumps(data_dump),
            properties=pika.BasicProperties(
                headers=headers
            )
        )
    except Exception as err:
        logger.error(f'ERROR - queue publishing error: {str(err)}')
        raise HTTPException(
            http.HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f'{http.HTTPStatus.INTERNAL_SERVER_ERROR}: Internal server error. Please try later.',
        )

    return {'notification_id': str(notification_id)}


@app.post('/api/add_template/', status_code=http.HTTPStatus.CREATED)
async def add_template(data: Template_schema, db_session: AsyncSession = Depends(get_session)):
    try:
        await Template(data).add_template(db_session)
    except Exception as err:
        logger.error(f'ERROR - cant create template: {str(err)}')
        raise HTTPException(
            http.HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f'{http.HTTPStatus.INTERNAL_SERVER_ERROR}: Internal server error. Please try later.',
        )
    return {http.HTTPStatus.CREATED: 'Template has been created'}


@app.get('/api/get_templates/', status_code=http.HTTPStatus.OK)
async def get_template(db_session: AsyncSession = Depends(get_session)):
    data = await Template.get_templates(db_session)
    return data


if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=9090,
    )
