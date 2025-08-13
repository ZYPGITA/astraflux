# -*- encoding: utf-8 -*-
import json
import pika

from astraflux.settings.keys import *

__all__ = ['initialization_rabbitmq', 'rabbitmq_send_message', 'rabbitmq_receive_message']

_RABBITMQ_URI = RABBITMQ.DEFAULT_VALUE_RABBITMQ_URI
_MQ_CHANNEL = None


def _parse_config():
    """
    Parse the RabbitMQ configuration string to extract host, port, user and password.

    Returns:
        tuple: A tuple containing host (str), port (int), user (str) and password (str).
    """
    parts = _RABBITMQ_URI.split('@')
    user_passwd = parts[0].split('//')[1]
    host_port = parts[1]

    user, passwd = user_passwd.split(':')
    host, port = host_port.split(':')

    return host, int(port), user, passwd


def _mq_channel():
    """
    Create and return a new RabbitMQ channel.

    Returns:
        pika.channel.Channel: A new channel object for interacting with RabbitMQ.
    """
    global _MQ_CHANNEL
    if _MQ_CHANNEL:
        return _MQ_CHANNEL

    host, port, user, passwd = _parse_config()
    credentials = pika.PlainCredentials(user, passwd)
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host, port=port, virtual_host='/', credentials=credentials, heartbeat=0))
    _MQ_CHANNEL = connection.channel()
    return _MQ_CHANNEL


def _create_queue(queue: str):
    """
    Create a queue in RabbitMQ. If an error occurs during creation, log the error.

    Args:
        queue (str): The name of the queue to create.

    Returns:
        pika.channel.Channel: The channel object used to create the queue.
    """
    _channel = _mq_channel()
    while True:
        try:
            _channel.queue_declare(queue=queue)
            break
        except Exception as e:
            try:
                global _MQ_CHANNEL
                _MQ_CHANNEL = None

                _channel = _mq_channel()
                _MQ_CHANNEL = _channel
                _channel.queue_declare(queue=queue)
                break
            except Exception as e:
                print('create_queue name == ', queue, ' error == ', e)

    return _channel


def initialization_rabbitmq(config: dict):
    """
    Initialize the logger with the given configuration.
    Args:
        config (dict): A dictionary containing the configuration.
    """
    global _RABBITMQ_URI
    _RABBITMQ_URI = config.get(RABBITMQ.KEY_RABBITMQ_URI)


def rabbitmq_send_message(queue: str, message: dict):
    """
    Send a message to a specified queue in RabbitMQ.

    Args:
        queue (str): The name of the queue to send the message to.
        message (dict): The message to send. It will be converted to a JSON string if it's not already.
    """
    _channel = _create_queue(queue=queue)
    if not isinstance(message, str):
        message = json.dumps(message)
    _channel.basic_publish(exchange='', routing_key=queue, body=message)


def rabbitmq_receive_message(queue: str, callback):
    """
    Start consuming messages from a specified queue in RabbitMQ.

    Args:
        queue (str): The name of the queue to consume messages from.
        callback (callable): The callback function to handle received messages.
    """
    _channel = _create_queue(queue=queue)
    _channel.basic_consume(on_message_callback=callback, queue=queue, auto_ack=False)
    _channel.start_consuming()


def register():
    from astraflux.interface import rabbitmq
    rabbitmq.rabbitmq_send_message = rabbitmq_send_message
    rabbitmq.rabbitmq_receive_message = rabbitmq_receive_message
    rabbitmq.initialization_rabbitmq = initialization_rabbitmq

    import sys
    sys.modules['astraflux.interface.rabbitmq'] = rabbitmq
