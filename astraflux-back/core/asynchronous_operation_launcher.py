# -*- encoding: utf-8 -*-

import sys
import json
import argparse

from astraflux.definitions.constants import *

from astraflux.inject import inject_init
from astraflux.interface.logger import get_logger
from astraflux.interface.core import init_global_vars
from astraflux.interface.rabbitmq import rabbitmq_receive_message

from astraflux.interface.data_access import (
    update_worker_and_service
)


class AsynchronousOperationLauncher:
    """
    Launcher for asynchronous operation components that process tasks from message queue.

    Handles worker registration, message queue listening, and
    task distribution to worker processes.
    """

    def __init__(self, class_path: str):
        """
        Initialize worker component launcher.

        Args:
            class_path: Path to worker class definition
        """
        self.class_path = class_path
        self.logger = get_logger(filename=PROJECT_NAME, task_id='AsynchronousOperationLauncher')

    def launch_asynchronous_operation(self):
        """
        Launch and run the asynchronous operation component.

        """

        rabbitmq_receive_message(
            queue=DEFINITIONS.RABBITMQ.QUEUE_NAME_ASYNCHRONOUS_OPERATION,
            callback=self._handle_incoming_message
        )

    def _handle_incoming_message(self, channel, method, properties, body):
        """
        Process incoming RabbitMQ messages and dispatch tasks.

        Args:
            channel: RabbitMQ channel object
            method: Delivery method information
            properties: Message properties
            body: Message body containing task data
        """
        # Acknowledge message receipt
        channel.basic_ack(delivery_tag=method.delivery_tag)

        try:
            task_data = json.loads(body.decode())

            self.logger.info(task_data)

        except Exception as processing_error:
            self.logger.error(f'Message processing error: {processing_error}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Distributed Worker Component Launcher")

    # Define command line arguments
    parser.add_argument("--yaml_file", type=str, required=True,
                        help="Path to YAML configuration file")
    parser.add_argument("--class_path", type=str, required=True,
                        help="Path to worker class definition file")
    parser.add_argument("--root_path", type=str, required=True,
                        help="Root path of the application")
    parser.add_argument("--current_dir", type=str, required=True,
                        help="Current working directory")

    # Parse arguments
    args = parser.parse_args()

    # Add current directory to Python path for module discovery
    sys.path.append(args.current_dir)
    sys.path.append(args.root_path)

    # Initialize dependency injection system
    inject_init(root_path=args.root_path)

    # Initialize global variables and configuration
    init_global_vars(
        yaml_file=args.yaml_file,
        current_dir=args.current_dir,
        root_path=args.root_path
    )

    # Launch the asynchronous operationLauncher component
    AsynchronousOperationLauncher(class_path=args.class_path).launch_asynchronous_operation()
