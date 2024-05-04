from datetime import datetime
import json
import logging
import smtplib
import sys

from jinja2 import Environment, BaseLoader
from jinja2.exceptions import TemplateError
from pika import BlockingConnection, ConnectionParameters, PlainCredentials
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import BasicProperties, Basic
from sqlalchemy import Column, Integer, String, Text, ARRAY, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.dialects.postgresql import UUID

from settings import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)

Base = declarative_base()


class Template(Base):
    __tablename__ = 'templates'
    id = Column(UUID(as_uuid=True), primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    text = Column(Text, nullable=False)
    variables = Column(ARRAY(String))
    version = Column(Integer, nullable=False)


def handler(ch: BlockingChannel, method: Basic.Deliver, properties: BasicProperties, body: bytes) -> None:
    data = json.loads(body.decode())
    notification = {
        'notification_id': data['notification_id'],
        'attempt_at': str(datetime.now())
    }
    try:
        template = get_template(data['template_name'], data['version'])
        rendered_template = parse_jinja(template, data['variables'])
        sendmail(data['emails'], rendered_template)
        notification['status'] = 'sent'
    except ConnectionError as e:
        logger.error(f'Connection problems with auth service: {e}')
        notification['status'] = 'error'
        ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
    except TemplateError as e:
        logger.error(f'Render error: {e}')
        notification['status'] = 'error'
        ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
    except (smtplib.SMTPAuthenticationError, OSError) as e:
        logger.error(f'Authentification error: {e}')
        notification['status'] = 'error'
        ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
    finally:
        ch.basic_publish(
            exchange=settings.exchange_out,
            routing_key='',
            body=json.dumps(notification)
        )
        if notification.get('status') == 'error':
            return
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
    return object.text


def parse_jinja(template_str, variables):
    env = Environment(loader=BaseLoader())
    template = env.from_string(template_str)
    if variables:
        rendered_template = template.render(**variables)
    else:
        rendered_template = template.render()
    return rendered_template


def sendmail(emails: list,  msg: str) -> None:
    smtp_serv = smtplib.SMTP(settings.smtpStr, settings.smtpPort)
    smtp_serv.ehlo_or_helo_if_needed()
    smtp_serv.starttls()
    smtp_serv.ehlo()
    smtp_serv.login(settings.sender, settings.password)
    for recepient in emails:
        try:
            smtp_serv.sendmail(settings.sender, recepient, msg)
        except smtplib.SMTPException:
            logger.error(f'Cannot send email to email {recepient}')
    smtp_serv.quit() 


if __name__ == '__main__':
    credentials = PlainCredentials(settings.rabbit_user, settings.rabbit_password)
    connection = BlockingConnection(ConnectionParameters(host=settings.rabbit_host, credentials=credentials))
    channel = connection.channel()
    channel.basic_consume(queue=settings.queue_in, on_message_callback=handler, auto_ack=False)
    while True:
        channel.start_consuming()
