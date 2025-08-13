# -*- encoding: utf-8 -*-

import time
import pika
import pickle
import builtins
from pika.exceptions import ChannelClosed

from astraflux.settings import *
from astraflux.interface import *


class ServiceUnavailableError(Exception):

    def __init__(self, service_name):
        super().__init__(f"Service '{service_name}' is not available")
        self.service_name = service_name


class RpcClient:
    """
    A RabbitMQ RPC client for making remote procedure calls.
    Args:
        config (dict): A dictionary containing the RabbitMQ configuration.
            - 'RABBITMQ_URI' (str): The RabbitMQ URI in the format 'amqp://user:password@host:port'.
    Attributes:
        config (dict): The RabbitMQ configuration.
        host (str): The RabbitMQ host.
        port (int): The RabbitMQ port.
        user (str): The RabbitMQ username.
        passwd (str): The RabbitMQ password.
        credentials (pika.PlainCredentials): The RabbitMQ credentials.
        connection (pika.BlockingConnection): The RabbitMQ connection.
        channel (pika.BlockingChannel): The RabbitMQ channel.
        queue (str): The RabbitMQ queue name
    """

    def __init__(self, config: dict):
        self.config = config
        self.timeout = config.get(RPC.KEY_RPC_CALL_TIMEOUT, RPC.DEFAULT_VALUE_RPC_CALL_TIMEOUT)

        self._validate_config()

        self.response = None
        self.corr_id = snowflake_id()

        # get host, port, user, passwd
        self.host, self.port, self.user, self.passwd = self._parse_config()
        self.credentials = pika.PlainCredentials(self.user, self.passwd)

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

    def _validate_config(self):
        if not self.config.get(RABBITMQ.KEY_RABBITMQ_URI):
            raise ValueError("Missing RabbitMQ URI in config")

    def _create_connection(self):
        """
        Create a RabbitMQ connection using the provided configuration.
        Returns:
            pika.BlockingConnection: The RabbitMQ connection.
        """
        params = pika.ConnectionParameters(
            host=self.host,
            port=self.port,
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

    def _parse_config(self):
        """
        Parse the RabbitMQ configuration string to extract host, port, user and password.

        Returns:
            tuple: A tuple containing host (str), port (int), user (str) and password (str).
        """

        parts = self.config.get(RABBITMQ.KEY_RABBITMQ_URI).split('@')

        user_passwd = parts[0].split('//')[1]
        host_port = parts[1]

        user, passwd = user_passwd.split(':')
        host, port = host_port.split(':')

        return host, int(port), user, passwd

    def _on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = pickle.loads(body)

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
            body=pickle.dumps(request)
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
