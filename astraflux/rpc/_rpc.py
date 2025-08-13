# -*- encoding: utf-8 -*-

import pika
import pickle
from functools import wraps

from astraflux.settings.keys import *
from astraflux.rpc.client import RpcClient

_RPC_METHODS = {}
_AMQP_CONFIG = {
    RABBITMQ.KEY_RABBITMQ_URI: RABBITMQ.DEFAULT_VALUE_RABBITMQ_URI,
    RPC.KEY_RPC_CALL_TIMEOUT: RPC.DEFAULT_VALUE_RPC_CALL_TIMEOUT
}


def _parse_config():
    """
    Parse the RabbitMQ configuration string to extract host, port, user and password.

    Returns:
        tuple: A tuple containing host (str), port (int), user (str) and password (str).
    """

    parts = _AMQP_CONFIG.get(RABBITMQ.KEY_RABBITMQ_URI).split('@')

    user_passwd = parts[0].split('//')[1]
    host_port = parts[1]

    user, passwd = user_passwd.split(':')
    host, port = host_port.split(':')

    return host, int(port), user, passwd


def _start_consumer(queue_name, service_instance):
    """
    Start a RabbitMQ consumer.
    Args:
        queue_name (str): The name of the queue to consume from.
        service_instance (function): The function to be called when a message is received.
    """
    host, port, user, passwd = _parse_config()
    credentials = pika.PlainCredentials(user, passwd)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=host, port=port, credentials=credentials, heartbeat=600)
    )
    channel = connection.channel()

    channel.queue_declare(
        queue=queue_name,
        durable=True,
        arguments={'x-ha-policy': 'all'}
    )
    channel.basic_qos(prefetch_count=100)

    def callback(ch, method_frame, props, body):
        response = None
        try:
            data = pickle.loads(body)
            method_name = data['method']
            args = data.get('args', [])
            kwargs = data.get('kwargs', {})

            if method_name not in _RPC_METHODS:
                raise AttributeError(f"Method {method_name} not registered as RPC")

            method = getattr(service_instance, method_name)
            result = method(*args, **kwargs)
            response = pickle.dumps({
                'status': 'success',
                'result': result
            })
        except Exception as e:
            response = pickle.dumps({
                'status': 'error',
                'exception': str(e),
                'type': type(e).__name__
            })
        finally:
            ch.basic_ack(method_frame.delivery_tag)
            ch.basic_publish(
                exchange='',
                routing_key=props.reply_to,
                properties=pika.BasicProperties(
                    correlation_id=props.correlation_id,
                    delivery_mode=2
                ),
                body=response
            )

    channel.basic_consume(
        queue=queue_name,
        on_message_callback=callback,
        consumer_tag=f"{queue_name}_consumer"
    )

    channel.start_consuming()


def initialization_rpc_proxy(config: dict):
    """
    Initialize the logger with the given configuration.
    Args:
        config (dict): A dictionary containing the configuration.
    """
    global _AMQP_CONFIG
    _AMQP_CONFIG[RABBITMQ.KEY_RABBITMQ_URI] = config.get(
        RABBITMQ.KEY_RABBITMQ_CONFIG, RABBITMQ.DEFAULT_VALUE_RABBITMQ_URI)

    _AMQP_CONFIG[RPC.KEY_RPC_CALL_TIMEOUT] = config.get(
        RPC.DEFAULT_VALUE_RPC_CALL_TIMEOUT, RPC.DEFAULT_VALUE_RPC_CALL_TIMEOUT)


def generate_unique():
    """
    Generates a unique identifier.
    Returns:
        str: The generated identifier.
    """
    client = RpcClient(config=_AMQP_CONFIG)
    service_name = '{}_{}_{}'.format(KEY_PROJECT_NAME, RPC.KEY_SYSTEM_SERVICE_NAME, 'task_distribution')
    data = client.call(service_name=service_name, method_name='generate_id')
    return data


def remote_call(service_name: str, method_name: str, **params):
    """
    Makes a remote procedure call to the specified service and method with the given parameters.

    Args:
        service_name (str): The name of the service to call.
        method_name (str): The name of the method to call.
        **params: Arbitrary keyword arguments to pass to the method.

    Returns:
        Any: The result of the remote procedure call.
    """
    client = RpcClient(config=_AMQP_CONFIG)
    data = client.call(
        service_name=service_name,
        method_name=method_name,
        **params
    )
    return data


def proxy_call(service_name: str, method_name: str, **params):
    """
    Makes a remote procedure call to the specified service and method with the given parameters.

    Args:
        service_name (str): The name of the service to call.
        method_name (str): The name of the method to call.
        **params: Arbitrary keyword arguments to pass to the method.

    Returns:
        Any: The result of the remote procedure call.
    """
    client = RpcClient(config=_AMQP_CONFIG)
    _name = '{}_{}'.format(KEY_PROJECT_NAME, service_name)

    data = client.call(
        service_name=_name,
        method_name=method_name,
        **params
    )
    return data


def rpc_decorator(func):
    """
    Decorator for RPC functions.
    Args:
        func (function): The function to be decorated.
    Returns:
        function: The decorated function.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    global _RPC_METHODS
    _RPC_METHODS.setdefault(func.__name__)

    wrapper._is_rpc_func = True
    return wrapper


def service_running(service_cls, config):
    """
    Start a RabbitMQ consumer.
    Args:
        config (dict): The AMQP URL for the RabbitMQ server.
        service_cls (class): The function to be called when a message is received.
    """
    global _AMQP_CONFIG
    _AMQP_CONFIG = config

    service_instance = service_cls()
    service_name = getattr(service_instance, 'name', service_cls.__name__)
    _start_consumer(service_name, service_instance)


def register():
    from astraflux.interface import rpc
    rpc.initialization_rpc_proxy = initialization_rpc_proxy
    rpc.generate_unique = generate_unique
    rpc.remote_call = remote_call
    rpc.proxy_call = proxy_call
    rpc.rpc_decorator = rpc_decorator
    rpc.service_running = service_running

    import sys
    sys.modules['astraflux.interface.rpc'] = rpc
