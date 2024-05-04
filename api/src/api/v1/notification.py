from schema import Event, Template_schema
import uuid
import pika
import http
from config import settings
import json
import logging
from fastapi import APIRouter, HTTPException

logger = logging.getLogger('uvicorn')
router = APIRouter()

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

@router.post('send', status_code=http.HTTPStatus.CREATED, response_model=dict)
def put_notification_to_queue(data: Event):
    data_dump = data.model_dump()
    if data_dump['send_immediately']:
        routing_key = f'{settings.rabbit_key_prefix}register'

    else:
        routing_key = f'{settings.rabbit_key_prefix}time'
    headers = {'routing_key': routing_key}
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