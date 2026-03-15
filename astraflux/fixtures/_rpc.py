# -*- encoding: utf-8 -*-

import time
import pika
import dill
import builtins
from pika.exceptions import ChannelClosed

from astraflux.core import global_manager
from astraflux.definitions.constants import *


class ServiceUnavailableError(Exception):

    def __init__(self, service_name):
        super().__init__(f"Service '{service_name}' is not available")
        self.service_name = service_name


class RpcClient:
    """
    A RabbitMQ RPC client for making remote procedure calls.
    Attributes:
        credentials (pika.PlainCredentials): The RabbitMQ credentials.
        connection (pika.BlockingConnection): The RabbitMQ connection.
        channel (pika.BlockingChannel): The RabbitMQ channel.
        queue (str): The RabbitMQ queue name
    """

    def __init__(self, corr_id: str, config: dict):
        self.timeout = RPC.DEFAULT.RPC_CALL_TIMEOUT.value

        self.response = None
        self.corr_id = corr_id

        self._host = config[RABBITMQ.CONFIG.HOST.value]
        self._port = config[RABBITMQ.CONFIG.PORT.value]
        self._user = config[RABBITMQ.CONFIG.USERNAME.value]
        self._password = config[RABBITMQ.CONFIG.PASSWORD.value]

        self.credentials = pika.PlainCredentials(self._user, self._password)

        # create connection and channel
        self.connection = self._create_connection()
        self.channel = self.connection.channel()

        # create queue
        self.queue = self.channel.queue_declare(
            queue='',
            exclusive=True,
            auto_delete=True
        ).method.queue

        # consume response
        self.channel.basic_consume(
            queue=self.queue,
            on_message_callback=self._on_response,
            auto_ack=True
        )

    def _create_connection(self):
        """
        Create a RabbitMQ connection using the provided configuration.
        Returns:
            pika.BlockingConnection: The RabbitMQ connection.
        """
        params = pika.ConnectionParameters(
            host=self._host,
            port=self._port,
            credentials=self.credentials,
            heartbeat=600,
            connection_attempts=3,
            retry_delay=5
        )
        return pika.BlockingConnection(params)

    def _check_service_available(self, service_name):
        try:
            self.channel.queue_declare(
                queue=service_name,
                passive=True
            )
            return True
        except ChannelClosed as e:
            if e.args[0] == 404:
                return False
            raise

    @staticmethod
    def _raise_rpc_exception(error_info):
        """
        Raises an exception based on the provided error information.
        Args:
            error_info (dict): A dictionary containing error information.
                - 'type' (str): The type of the exception (e.g., 'TypeError', 'ValueError').
                - 'exception' (str): The exception message.
        Raises:
            TypeError: If the 'type' is 'TypeError'.
            ValueError: If the 'type' is 'ValueError'.
            KeyError: If the 'type' is 'KeyError'.
            AttributeError: If the 'type' is 'AttributeError'.
            RuntimeError: If the 'type' is not recognized or if there is an issue with the exception.
        """
        ex_type = error_info.get('type', 'RpcError')
        ex_msg = error_info.get('exception', 'Unknown RPC error')

        allowed_exceptions = [
            'TypeError', 'ValueError', 'KeyError',
            'AttributeError', 'RuntimeError', 'PermissionError'
        ]

        try:
            if ex_type in allowed_exceptions:
                exception_class = getattr(builtins, ex_type)
                if issubclass(exception_class, Exception):
                    raise exception_class(ex_msg)
            raise RuntimeError(ex_msg)

        except AttributeError:
            raise RuntimeError(ex_msg)

    def _on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = dill.loads(body)

    def call(self, service_name, method_name, *args, **kwargs):
        """
        Call a remote procedure on the specified service.
        Args:
            service_name (str): The name of the service to call.
            method_name (str): The name of the method to call on the service.
            *args: Positional arguments to pass to the method.
            **kwargs: Keyword arguments to pass to the method.
        Returns:
            Any: The result of the method call.
        Raises:
            ServiceUnavailableError: If the specified service is not available.
            TimeoutError: If the RPC call times out.
        """

        if not self._check_service_available(service_name):
            raise ServiceUnavailableError(service_name)

        request = {
            'method': method_name,
            'args': args,
            'kwargs': kwargs
        }

        self.channel.basic_publish(
            exchange='',
            routing_key=service_name,
            properties=pika.BasicProperties(
                reply_to=self.queue,
                correlation_id=self.corr_id,
                delivery_mode=2
            ),
            body=dill.dumps(request)
        )

        start_time = time.time()
        while self.response is None:
            if time.time() - start_time > self.timeout:
                raise TimeoutError("RPC call timed out")
            self.connection.process_data_events()

        if isinstance(self.response, dict):
            status = self.response.get('status')
            if status == 'error':
                self._raise_rpc_exception(self.response)
            if status == 'success':
                return self.response.get('result')
        return self.response


class RpcServer:

    def __init__(self, config):
        self._host = config[RABBITMQ.CONFIG.HOST.value]
        self._port = config[RABBITMQ.CONFIG.PORT.value]
        self._user = config[RABBITMQ.CONFIG.USERNAME.value]
        self._password = config[RABBITMQ.CONFIG.PASSWORD.value]

        self.credentials = pika.PlainCredentials(self._user, self._password)

        # create connection and channel
        self.connection = self._create_connection()
        self.channel = self.connection.channel()

    def _create_connection(self):
        """
        Create a RabbitMQ connection using the provided configuration.
        Returns:
            pika.BlockingConnection: The RabbitMQ connection.
        """
        params = pika.ConnectionParameters(
            host=self._host,
            port=self._port,
            credentials=self.credentials,
            heartbeat=600,
            connection_attempts=3,
            retry_delay=5
        )
        return pika.BlockingConnection(params)

    def start_consumer(self, queue_name, service_instance):
        """
        Start a RabbitMQ consumer.
        Args:
            queue_name (str): The name of the queue to consume from.
            service_instance (function): The function to be called when a message is received.
        """
        self.channel.queue_declare(
            queue=queue_name,
            durable=True,
            arguments={'x-ha-policy': 'all'}
        )
        self.channel.basic_qos(prefetch_count=100)

        def callback(ch, method_frame, props, body):
            response = None
            try:
                data = dill.loads(body)
                method_name = data['method']
                args = data.get('args', [])
                kwargs = data.get('kwargs', {})

                method = getattr(service_instance(), method_name)
                result = method(*args, **kwargs)
                response = dill.dumps({
                    'status': 'success',
                    'result': result
                })
            except Exception as e:
                response = dill.dumps({
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

        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=callback,
            consumer_tag=f"{queue_name}_consumer"
        )

        self.channel.start_consuming()


@global_manager.register_fixture(name="fixture_rpc_client", scope=Scope.THREAD)
def _rpc_client(fixture_config, fixture_generate_id):
    """
    Create a RabbitMQ RPC client.
    Args:
        fixture_config: The configuration for the RPC client.
        fixture_generate_id : The id of the fixture.
    Returns:
        RpcClient: The RabbitMQ RPC client.
    """
    _corr_id = fixture_generate_id.snowflake_id()
    _rabbitmq_config = fixture_config[RABBITMQ.CONFIG.KEY.value]

    rpc_client = RpcClient(corr_id=_corr_id, config=_rabbitmq_config)
    yield rpc_client
    rpc_client.connection.close()


@global_manager.register_fixture(name="fixture_rpc_server", scope=Scope.THREAD)
def _rpc_server(fixture_config):
    """
    Create a RabbitMQ RPC server.
    Args:
        fixture_config: The configuration for the RPC server.
    Returns:
        RpcServer: The RabbitMQ RPC server.
    """
    _rabbitmq_config = fixture_config[RABBITMQ.CONFIG.KEY.value]

    rpc_server = RpcServer(config=_rabbitmq_config)
    yield rpc_server
    rpc_server.connection.close()
