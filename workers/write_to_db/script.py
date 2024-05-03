from datetime import datetime
import json
import logging
import sys

from pika import BlockingConnection, ConnectionParameters, PlainCredentials
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import BasicProperties, Basic
from sqlalchemy import Column, String, ARRAY, create_engine, DateTime, ForeignKey, Integer
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.dialects.postgresql import UUID

from settings import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)

Base = declarative_base()


class Notification(Base):
    __tablename__ = 'notifications'
    notification_id = Column(UUID(as_uuid=True), primary_key=True)
    template_name = Column(String(255), nullable=False)
    user_ids = Column(ARRAY(UUID))
    version = Column(Integer)
    create_at = Column(DateTime, default=datetime.now)


class History(Base):
    __tablename__ = 'history'
    notification_id = Column(UUID(as_uuid=True), ForeignKey('notifications.notification_id'), primary_key=True)
    status = Column(String(255), nullable=False)
    attempt_at = Column(DateTime, default=datetime.now)


def handler(ch: BlockingChannel, method: Basic.Deliver, properties: BasicProperties, body: bytes) -> None:
    data = json.loads(body.decode())
    dsn = settings.psql_dsn
    engine = create_engine(
        str(dsn),
        connect_args={'options': '-csearch_path={}'.format('notification')}
    )
    Session = sessionmaker(engine)
    with Session() as session:
        try:
            if data.get('status'):
                new_obj = History(**data)
            else:
                new_obj = Notification(
                    notification_id=data['notification_id'],
                    template_name=data['template_name'],
                    version=data['version'],
                    user_ids=data['user_ids'],
                )
            session.add(new_obj)
            session.commit()
            logger.info('Object was saved')
        except ConnectionError as e:
            logging.error(f'Connection problems with auth service: {e}')
            ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
            return
    ch.basic_ack(delivery_tag=method.delivery_tag)


if __name__ == '__main__':
    credentials = PlainCredentials(settings.rabbit_user, settings.rabbit_password)
    connection = BlockingConnection(ConnectionParameters(host=settings.rabbit_host, credentials=credentials))
    channel = connection.channel()
    channel.basic_consume(queue=settings.queue_in, on_message_callback=handler, auto_ack=False)
    while True:
        channel.start_consuming()
