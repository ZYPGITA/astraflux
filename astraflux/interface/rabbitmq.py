# -*- encoding: utf-8 -*-
from astraflux.inject import inject_implementation

__all__ = ['initialization_rabbitmq', 'rabbitmq_send_message', 'rabbitmq_receive_message']


@inject_implementation()
def initialization_rabbitmq(config: dict):
    """
    Initialize the logger with the given configuration.
    Args:
        config (dict): A dictionary containing the configuration.
    """


@inject_implementation()
def rabbitmq_send_message(queue: str, message: dict):
    """
    Send a message to a specified queue in RabbitMQ.

    Args:
        queue (str): The name of the queue to send the message to.
        message (dict): The message to send. It will be converted to a JSON string if it's not already.
    """


@inject_implementation()
def rabbitmq_receive_message(queue: str, callback):
    """
    Start consuming messages from a specified queue in RabbitMQ.

    Args:
        queue (str): The name of the queue to consume messages from.
        callback (callable): The callback function to handle received messages.
    """
