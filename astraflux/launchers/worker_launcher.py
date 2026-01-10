# -*- encoding: utf-8 -*-

import os
import sys
import time
import json
import argparse
import multiprocessing


class TaskExecutor:
    """
    Executes individual tasks in isolated worker processes.

    Handles task lifecycle including initialization, execution,
    status tracking, and cleanup.
    """

    @staticmethod
    def execute_task(task_data: dict, class_path: str, yaml_config: str, current_dir: str):
        """
        Execute a single task in an isolated worker process.

        Args:
            task_data: Dictionary containing task parameters and data
            class_path: Path to worker class definition
            yaml_config: Path to YAML configuration file
            current_dir: Current working directory
        """

        AstraFlux(yaml_path=yaml_config, current_dir=current_dir)

        worker_process_id = os.getpid()

        # Build worker component for task execution
        worker_builder = Build(
            class_path=class_path,
            component_type='worker',
            constructor=WorkerConstructor
        )
        worker_component = worker_builder.build_component(
            task_id=task_data[TASK.CONFIG.ID.value]
        )

        # Update task status to running
        TaskExecutor._update_task_status(
            worker_component, task_data, worker_process_id,
            STATUS.RUNNING.value
        )

        try:
            # Register worker as running
            redis_add_to_run_process(
                unique_id=worker_component.unique_id,
                process_id=worker_process_id
            )

            # Execute the task
            worker_component().run(task_data)

            # Mark task as successfully completed
            TaskExecutor._update_task_status(
                worker_component, task_data, worker_process_id,
                STATUS.SUCCESS.value
            )

        except Exception as execution_error:
            # Mark task as failed and record error
            TaskExecutor._update_task_status(
                worker_component, task_data, worker_process_id,
                STATUS.FAILED.value
            )
            worker_component.logger.error(
                f"Task execution failed: {execution_error}"
            )
        finally:
            # Cleanup worker registration
            redis_remove_from_run_process(
                unique_id=worker_component.unique_id,
                process_id=worker_process_id
            )

    @staticmethod
    def _update_task_status(worker_component, task_data: dict, worker_pid: int, status):
        """
        Update task status in the task tracking system.

        Args:
            worker_component: Worker component instance
            task_data: Task data dictionary
            worker_pid: Worker process ID
            status: New task status
        """

        current_time = converted_time()
        update_data = {
            BUILD.CONFIG.WORKER_PID: worker_pid,
            BUILD.CONFIG.WORKER_IPADDR: worker_component.ipaddr,
            TASK.CONFIG.STATUS.value: status,
        }

        # Add timing information based on status
        if status == STATUS.RUNNING.value:
            update_data[TASK.CONFIG.START_TIME.value] = current_time
        else:
            update_data[TASK.CONFIG.END_TIME.value] = current_time

        rabbitmq_send_message(
            queue=DEFINITIONS.RABBITMQ.QUEUE_NAME_ASYNCHRONOUS_OPERATION,
            message={
                'method': 'update_running_worker',
                'task_data': task_data,
                'update_data': update_data,
            }
        )


class MessageQueueHandler:
    """
    Handles RabbitMQ message processing and task distribution.

    Listens for incoming task messages, validates them, and
    dispatches to available worker processes with load balancing.
    """

    def __init__(self, class_path: str, yaml_config: str, current_dir: str,
                 root_path: str, logger, ipaddr: str, worker_name: str):
        """
        Initialize message queue handler.

        Args:
            class_path: Path to worker class definition
            yaml_config: Path to YAML configuration file
            current_dir: Current working directory
            root_path: Root application directory
            logger: Logger instance for message handling
            ipaddr: Worker IP address
            worker_name: Worker component name
        """
        self.class_path = class_path
        self.yaml_config = yaml_config
        self.current_dir = current_dir
        self.root_path = root_path
        self.logger = logger
        self.ipaddr = ipaddr
        self.worker_name = worker_name

    def handle_incoming_message(self, channel, method, properties, body):
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

            # Validate task data contains required ID
            if DEFINITIONS.TASK.ID not in task_data:
                self.logger.error(f'Invalid task data missing ID: {task_data}')
                return

            # Dispatch task for execution
            self._dispatch_task_to_worker(task_data, channel, body)

        except Exception as processing_error:
            self.logger.error(f'Message processing error: {processing_error}')

    def _dispatch_task_to_worker(self, task_data: dict, channel, body):
        """
        Dispatch task to available worker process with capacity checking.

        Args:
            task_data: Task data dictionary
            channel: RabbitMQ channel for requeueing if needed
            body: Original message body
        """
        # Check if task should be executed
        if not self._should_execute_task(task_data):
            return

        # Check worker capacity
        if not self._has_available_worker_capacity():
            # Requeue task if no capacity available
            time.sleep(0.2)
            channel.basic_publish(
                body=body,
                exchange='',
                routing_key=self.worker_name
            )
            return

        # Execute task in separate process
        self._execute_task_in_isolated_process(task_data)

    def _should_execute_task(self, task_data: dict) -> bool:
        """
        Determine if task should be executed based on current status.

        Args:
            task_data: Task data dictionary

        Returns:
            Boolean indicating if task should be executed
        """

        # System services always execute
        if DEFINITIONS.SYSTEM_SERVICE_NAME in self.worker_name:
            return True

        # Check task status from Redis
        task_status = task_status_get_from_redis(
            task_id=task_data.get(DEFINITIONS.TASK.ID)
        )
        return task_status != DEFINITIONS.STATUS.STOPPED

    def _has_available_worker_capacity(self) -> bool:
        """
        Check if worker has capacity to handle new tasks.

        Returns:
            Boolean indicating if worker has available capacity
        """

        current_workers, max_workers = redis_get_available_slots(
            name=self.worker_name,
            ipaddr=self.ipaddr
        )
        return current_workers < max_workers

    def _execute_task_in_isolated_process(self, task_data: dict):
        """
        Execute task in a separate isolated process.

        Args:
            task_data: Task data dictionary
        """
        worker_process = multiprocessing.Process(
            target=TaskExecutor.execute_task,
            args=(
                task_data, self.class_path, self.yaml_config,
                self.current_dir, self.root_path
            )
        )
        worker_process.daemon = True
        worker_process.start()


class WorkerComponentLauncher:
    """
    Launcher for worker components that process tasks from message queue.

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

    def launch_worker(self):
        """
        Launch and run the worker component.

        This method:
        1. Builds and registers the worker component
        2. Starts listening for messages from RabbitMQ
        3. Handles task distribution with fault tolerance
        """
        # Build worker component
        worker_builder = Build(
            class_path=self.class_path,
            component_type='worker',
            constructor=WorkerConstructor
        )
        worker_component = worker_builder.build_component()

        # Register worker in service discovery
        self._register_worker_component(worker_component)

        # Start message processing loop
        self._start_message_processing(worker_component)

    @staticmethod
    def _register_worker_component(worker_component):
        """
        Register worker component in the service discovery system.

        Args:
            worker_component: Configured worker component instance
        """
        worker_registration_data = {
            BUILD.CONFIG.UNIQUE_ID.value: worker_component.unique_id,
            BUILD.CONFIG.NAME.value: worker_component.name,
            BUILD.CONFIG.WORKER_IPADDR.value: worker_component.ipaddr,
            BUILD.CONFIG.WORKER_NAME.value: worker_component.worker_name,
            BUILD.CONFIG.WORKER_VERSION.value: worker_component.version,
            BUILD.CONFIG.WORKER_PID.value: os.getpid(),
            BUILD.CONFIG.WORKER_FUNCTIONS.value: worker_component.functions,
            BUILD.CONFIG.WORKER_MAX_PROCESS.value: 10,
            BUILD.CONFIG.WORKER_RUN_PROCESS.value: []
        }

        redis_store_worker_data(data=worker_registration_data)

        worker_component.logger.info(f'Worker component started: {worker_registration_data}')

    @staticmethod
    def _start_message_processing(worker_component):
        """
        Start listening for and processing messages from RabbitMQ.

        Args:
            worker_component: Worker component instance
        """
        # Initialize message queue handler
        message_handler = MessageQueueHandler(
            class_path=args.class_path,
            yaml_config=args.yaml_file,
            current_dir=args.current_dir,
            root_path=args.root_path,
            logger=worker_component.logger,
            ipaddr=worker_component.ipaddr,
            worker_name=worker_component.worker_name
        )

        # Main message processing loop with error handling
        while True:
            try:
                rabbitmq_receive_message(
                    queue=worker_component.worker_name,
                    callback=message_handler.handle_incoming_message
                )
            except Exception as connection_error:
                worker_component.logger.error(
                    f'Worker {worker_component.worker_name} connection error: {connection_error}'
                )
                time.sleep(0.5)  # Prevent tight loop on persistent errors


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Distributed Worker Component Launcher")

    # Define command line arguments
    parser.add_argument("--yaml_file", type=str, required=True,
                        help="Path to YAML configuration file")
    parser.add_argument("--class_path", type=str, required=True,
                        help="Path to service class definition file")
    parser.add_argument("--current_dir", type=str, required=True,
                        help="Current working directory")

    # Parse arguments
    args = parser.parse_args()

    from astraflux import AstraFlux
    from astraflux.definitions.constants import *
    from astraflux.definitions.constructor import WorkerConstructor

    AstraFlux(yaml_path=args.yaml_file, current_dir=args.current_dir)

    # Add current directory to Python path for module discovery
    sys.path.append(args.current_dir)

    from .build import Build

    from astraflux.interface import (
        redis_store_worker_data, rabbitmq_receive_message, redis_add_to_run_process,
        redis_remove_from_run_process, converted_time, redis_get_available_slots
    )

    # Launch the worker component
    WorkerComponentLauncher(class_path=args.class_path).launch_worker()
