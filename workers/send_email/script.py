import json
import logging
import sys

from jinja2 import Environment, BaseLoader
from jinja2.exceptions import TemplateError
from pika import BlockingConnection, ConnectionParameters, PlainCredentials
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import BasicProperties, Basic
from sqlalchemy import Column, Integer, String, Text, ARRAY, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from settings import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)

Base = declarative_base()


class Template(Base):
    __tablename__ = 'templates'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    template = Column(Text, nullable=False)
    variables = Column(ARRAY(String))
    version = Column(Integer, nullable=False)


def handler(ch: BlockingChannel, method: Basic.Deliver, properties: BasicProperties, body: bytes) -> None:
    data = json.loads(body.decode())
    try:
        template = get_template(data['template'], data['version'])
        rendered_template = parse_jinja(template, data['variables'])
        ch.basic_publish(
            exchange=settings.exchange_out,
            routing_key='',
            body=body
        )
    except ConnectionError as e:
        logger.error(f'Connection problems with auth service: {e}')
        ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
    except TemplateError as e:
        logger.error(f'Render error: {e}')
        ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
    logger.info(rendered_template)
    ch.basic_ack(delivery_tag=method.delivery_tag)


def get_template(template_name, version):
    dsn = settings.psql_dsn
    engine = create_engine(
        str(dsn),
        connect_args={'options': '-csearch_path={}'.format('template')}
    )
    Session = sessionmaker(engine)
    with Session() as session:
        object = session.query(Template).filter_by(name=template_name, version=version).first()
    return object.template


def parse_jinja(template_str, variables):
    env = Environment(loader=BaseLoader())
    template = env.from_string(template_str)
    rendered_template = template.render(**variables)
    return rendered_template


if __name__ == '__main__':
    credentials = PlainCredentials(settings.rabbit_user, settings.rabbit_password)
    connection = BlockingConnection(ConnectionParameters(host=settings.rabbit_host, credentials=credentials))
    channel = connection.channel()
    channel.basic_consume(queue=settings.queue_in, on_message_callback=handler, auto_ack=False)
    while True:
        channel.start_consuming()
