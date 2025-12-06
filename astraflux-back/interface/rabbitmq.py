# -*- encoding: utf-8 -*-


def rabbitmq_send_message(queue: str, message: dict):
    """
    Send a message to a specified queue in RabbitMQ.

    Args:
        queue (str): The name of the queue to send the message to.
        message (dict): The message to send. It will be converted to a JSON string if it's not already.
    """
    return rabbitmq_send_message(queue, message)


def rabbitmq_receive_message(queue: str, callback):
    """
    Start consuming messages from a specified queue in RabbitMQ.

    Args:
        queue (str): The name of the queue to consume messages from.
        callback (callable): The callback function to handle received messages.
    """
    return rabbitmq_receive_message(queue, callback)
