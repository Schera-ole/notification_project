from datetime import datetime
import json
import logging

from pika import BlockingConnection, ConnectionParameters, PlainCredentials
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import BasicProperties, Basic

from settings import settings


def handler(ch: BlockingChannel, method: Basic.Deliver, properties: BasicProperties, body: bytes) -> None:
    data = json.loads(body.decode())
    send_time = data.get('send_time')
    datetime_send_time = datetime.strptime(send_time, "%Y-%m-%d %H:%M:%S")
    now_time = datetime.now()
    routing_prefix = properties.headers['routing_key'].rsplit(".", 1)
    try:
        if datetime_send_time > now_time:
            ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
            return
        elif datetime_send_time <= now_time:
            ch.basic_publish(
                exchange=settings.exchange_out,
                routing_key=f'{routing_prefix}.register',
                body=json.dumps(data)
            )
    except ConnectionError as e:
        logging.error(f'Connection problems with auth service: {e}')
        ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
    ch.basic_ack(delivery_tag=method.delivery_tag)


if __name__ == '__main__':
    credentials = PlainCredentials(settings.rabbit_user, settings.rabbit_password)
    connection = BlockingConnection(ConnectionParameters(host=settings.rabbit_host, credentials=credentials))
    channel = connection.channel()
    channel.basic_consume(queue=settings.queue_in, on_message_callback=handler, auto_ack=False)
    while True:
        channel.start_consuming()
