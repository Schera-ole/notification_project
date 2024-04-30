import json
import logging
import sys

from pika import BlockingConnection, ConnectionParameters, PlainCredentials
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import BasicProperties, Basic
import requests

from settings import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)


def handler(ch: BlockingChannel, method: Basic.Deliver, properties: BasicProperties, body: bytes) -> None:
    data = json.loads(body.decode())
    data['emails'] = []
    user_ids = data.get('user_ids')
    try:
        for user_id in user_ids:
            user_email = get_user_info(user_id)
            data['emails'].append(user_email)
        ch.basic_publish(
            exchange=settings.exchange_out,
            routing_key='',
            body=body
        )
    except ConnectionError as e:
        logger.error(f'Connection problems with auth service: {e}')
        ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
    ch.basic_ack(delivery_tag=method.delivery_tag)


def get_user_info(user_id):
    url = settings.auth_url
    response = requests.get(f'{url}?user_id={user_id}')
    data = response.json()
    user_email = data.get('email')
    return user_email


if __name__ == '__main__':
    credentials = PlainCredentials(settings.rabbit_user, settings.rabbit_password)
    connection = BlockingConnection(ConnectionParameters(host=settings.rabbit_host, credentials=credentials))
    channel = connection.channel()
    channel.basic_consume(queue=settings.queue_in, on_message_callback=handler, auto_ack=False)
    while True:
        channel.start_consuming()
