AstraFlux Framework Documentation
==================================

1. Introduction
---------------

AstraFlux Framework is designed to help developers quickly build distributed task management
and microservice systems, providing convenient functionalities such as service registration,
RPC calls, task distribution and processing.


2. Directory Structure
----------------------

The recommended project directory structure is as follows::

    project_root/
    ├── servers/
    │   ├── test_server.py       # Test service implementation
    │   └── sub_test_server.py   # Sub-test service implementation
    ├── main.py                  # Service startup script
    ├── test.py                  # Function test script
    └── config.yaml              # Configuration file

3. Configuration File
---------------------

Create a ``config.yaml`` configuration file with the following content::

    mongodb:
      host: 127.0.0.1
      port: 27017
      db: astraflux  # Default database name
      username: scheduleAdmin
      password: scheduleAdminPassword

    redis:
      host: 127.0.0.1
      port: 6379
      password: scheduleAdminPassword

    rabbitmq:
      host: 127.0.0.1
      port: 5672
      username: scheduleAdmin
      password: scheduleAdminPassword

    logger:
      path: logs  # Log saving path (working directory + this path)
      level: INFO  # Log level


4. Service Implementation
-------------------------

4.1 Basic Service Structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Services need to implement two types of core components:
- Subclass of ``ServiceConstructor``: Provides RPC interfaces
- Subclass of ``WorkerConstructor``: Processes distributed tasks

4.2 Test Service Example (test_server.py)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    # -*- coding: utf-8 -*-
    import time

    from astraflux import ServiceConstructor, WorkerConstructor, rpc_decorator


    class RpcFunction(ServiceConstructor):
        """RPC service implementation class"""
        service_name = 'test_server'  # Unique service identifier

        @rpc_decorator  # Mark as a remotely callable method
        def get_service_name(self):
            """Get service information"""
            return {"service_version": self.ipaddr}

        @rpc_decorator
        def test_func(self, **args):
            """Test RPC method, return incoming parameters"""
            return args


    class WorkerFunction(WorkerConstructor):
        """Task processing class"""
        worker_name = 'test_server'  # Bound task queue name

        def run(self, data):
            """Core method for processing tasks"""
            self.logger.info(f"Received task: {data}")
            time.sleep(5)  # Simulate task processing time
            self.logger.info(f"Task completed: {data['task_id']}")

4.3 Sub-test Service Example (sub_test_server.py)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Consistent with the structure of ``test_server.py``, only the service identifier needs to be modified::

    # -*- coding: utf-8 -*-
    import time

    from astraflux import ServiceConstructor, WorkerConstructor, rpc_decorator


    class RpcFunction(ServiceConstructor):
        service_name = 'sub_test_server'  # Sub-service name

        @rpc_decorator
        def get_service_name(self):
            return {"service_version": self.ipaddr}

        @rpc_decorator
        def test_func(self,** args):
            return args


    class WorkerFunction(WorkerConstructor):
        worker_name = 'sub_test_server'  # Sub-service task queue name

        def run(self, data):
            self.logger.info(data)
            time.sleep(3)
            self.logger.info(f"sub worker done {data['task_id']}")

5. Service Startup Script (main.py)
-----------------------------------

Used to register and start services::

    # -*- coding: utf-8 -*-
    import os

    from astraflux import AstraFlux

    # Import custom services
    from servers import test_server, sub_test_server

    if __name__ == "__main__":
        # Get current directory
        current_dir = os.path.dirname(__file__)

        # Initialize the framework (load configuration file)
        af = AstraFlux(
            yaml_file=f'{current_dir}/config.yaml',
            current_dir=current_dir
        )

        # Register service list
        af.registry(services=[test_server, sub_test_server])

        # Start services (wait=True means blocking the main process)
        af.start(wait=True)

6. Function Testing (test.py)
-----------------------------

Used to test RPC calls and task submission::

    from astraflux import proxy_call, task_submit_to_db, subtask_batch_create, snowflake_id
    import os

    if __name__ == "__main__":
        current_dir = os.path.dirname(__file__)

        # Initialize the framework (load configuration)
        af = AstraFlux(
            yaml_file=f'{current_dir}/config.yaml',
            current_dir=current_dir
        )

        # 1. Test RPC call
        rpc_result = proxy_call(
            service_name='test_server',  # Target service name
            method_name='test_func',     # Target method name
            x=1, y=2                     # Incoming parameters
        )
        print("RPC call result:", rpc_result)

        # 2. Submit main tasks and subtasks
        for i in range(3):
            # Generate unique task ID
            main_task_id = snowflake_id()

            # Submit main task to test_server queue
            task_submit_to_db(
                queue_name='test_server',
                task_data={'task_id': main_task_id, 'index': i}
            )

            # Create 5 subtasks for each main task (submitted to sub_test_server queue)
            # The scheduler will automatically monitor the status of subtasks and update the source task
            # automatically after all subtasks are completed
            subtask_ids = subtask_batch_create(
                source_task_id=main_task_id,  # Associated main task ID
                subtask_queue='sub_test_server',  # Subtask queue
                subtask_list=[{'task_id': f'{main_task_id}_{j}', 'parent': main_task_id} for j in range(5)]
            )
            print(f"Subtask IDs of main task {main_task_id}:", subtask_ids)

7. Distributed Deployment
-------------------------

7.1 Multi-machine Deployment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When deploying services on different machines, only need to modify the registered service list in ``main.py``::

    # Start only test_server
    af.registry(services=[test_server])

    # Or start only sub_test_server
    af.registry(services=[sub_test_server])

7.2 Load Balancing
~~~~~~~~~~~~~~~~~~

The framework will automatically perform load balancing for instances with the same service name, and each task will be
assigned to only one service instance for execution.

7.3 Adjust Worker Quantity
~~~~~~~~~~~~~~~~~~~~~~~~~~

The maximum number of workers for a specified service instance can be adjusted through the following method::

    from astraflux import update_max_worker

    # Modify the maximum number of workers for the test_server service (127.0.0.1 instance) to 10
    update_max_worker(name='test_server', ipaddr='127.0.0.1', max_worker=10)

8. Scheduler API
----------------

    Support local process/thread task management and distributed scheduling::

        # distributed scheduler
        add_schedule_job(
            job_id='test_001',
            cron_expression='*/10 * * * * *',
            function=test_func,
            keyword_arguments={'x': 2},
            execution_type='thread'  # thread or process
        )

        af.registry(services=[test_server, sub_test_server])
        af.start(wait=False) # Simultaneously enable the scheduler and asynchronous tasks, set to False

        # If both the scheduler and asynchronous tasks are enabled, the distributed scheduler needs to be started first
        # Asynchronous task scheduler, supporting processes/threads
        from astraflux import gen_thread_executor, gen_process_executor

        executor = gen_thread_executor(logger=logger, max_workers=20, retry_delay=1)
        # executor = gen_process_executor(logger=logger, max_workers=20, retry_delay=1)

        def test_func(x):
            while True:
                print(x)

        # Submit a task to the executor
        executor.submit(test_func, 1)

        # Start the executor
        executor.start()

        # Wait for all tasks to complete
        executor.wait_completion()

        # Shutdown the executor
        executor.shutdown()



8. API Reference
-----------------

8.1 ``interface/definitions.py``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ``set_root_path(root_path: str)``: Sets the root directory for global variables.
- ``get_root_path()``: Gets the root directory for global variables.
- ``set_current_dir(current_dir: str)``: Sets the current directory for global variables.
- ``get_current_dir() -> str | None``: Gets the current directory for global variables.
- ``set_rabbitmq_uri(uri: str)``: Sets the RabbitMQ URI for global variables.
- ``get_rabbitmq_uri() -> str | None``: Gets the RabbitMQ URI for global variables.
- ``set_redis_uri(redis_uri: str)``: Sets the Redis URI for global variables.
- ``get_redis_uri() -> str | None``: Gets the Redis URI for global variables.
- ``set_mongo_uri(mongo_uri: str)``: Sets the Mongo URI for global variables.
- ``get_mongo_uri() -> str | None``: Gets the Mongo URI for global variables.
- ``set_logs_path(logs_path: str)``: Sets the logs path for global variables.
- ``get_logs_path() -> str | None``: Gets the logs path for global variables.
- ``set_log_level(log_level: str) -> None``: Sets the log level for global variables.
- ``get_log_level() -> str | None``: Gets the log level for global variables.

8.2 ``interface/rpc.py``
~~~~~~~~~~~~~~~~~~~~~~~~~

- ``generate_unique()``: Generates a unique identifier, returns the generated identifier string.
- ``remote_call(service_name: str, method_name: str, **params)``: Makes a remote procedure call to the specified service and method, returns the call result.
- ``proxy_call(service_name: str, method_name: str,** params)``: Makes a remote procedure call to the specified service and method, returns the call result.
- ``rpc_decorator(func)``: RPC function decorator, returns the decorated function.
- ``service_running(service_cls)``: Starts the RabbitMQ consumer, the parameter is the class corresponding to the function to be called when a message is received.


8.4 ``interface/rabbitmq.py``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ``rabbitmq_send_message(queue: str, message: dict)``: Sends a message to the specified queue in RabbitMQ; if the message is not a JSON string, it will be converted.
- ``rabbitmq_receive_message(queue: str, callback)``: Consumes messages from the specified queue in RabbitMQ and processes the received messages through a callback function.

8.5 ``interface/logger.py``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ``get_logger(filename: str = None, task_id: str = None) -> logging.Logger``: Gets a logger instance, which can specify the log file name and task ID.

8.6 ``interface/executor.py``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ``gen_thread_executor(logger, max_workers: int = 5, retry_delay: float = 1.0) -> ThreadPoolExecutorWithRetry``: Factory function for creating ``ThreadPoolExecutorWithRetry`` instances.
- ``gen_process_executor(logger, max_workers: int = 5, retry_delay: float = 1.0) -> ProcessPoolExecutorWithRetry``: Factory function for creating ``ProcessPoolExecutorWithRetry`` instances.

8.7 ``interface/utils.py``
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ``get_date_time_obj(data_str: str, fmt=False, timezone=False)``: Returns a time object according to the specified timezone and format.
- ``format_converted_time(data_str: str, fmt=False, timezone=False, r_fmt=False)``: Formats the time string according to the specified format and timezone.
- ``get_converted_time(fmt=False, timezone=False)``: Specifies the timezone and format, returns the current time string.
- ``convert_timestamp_to_timezone(timestamp, fmt=False, timezone=False)``: Converts the timestamp to a time string in the specified timezone and format.
- ``get_converted_timestamp(date_string: str, fmt=False, timezone=False)``: Converts the time string to a timestamp in the specified timezone and format.
- ``convert_timestamp_to_timezone_str(timestamp, timezone=False, fmt=False)``: Converts the timestamp to a time string.
- ``get_ipaddr() -> str``: Retrieves the IP address of the current machine by establishing a UDP connection.

8.8 ``interface/snowflake.py``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ``snowflake_id() -> str``: Returns a snowflake ID generation function.

8.9 ``interface/data_access.py``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ``MongoDBCollector`` class: MongoDB collection operation wrapper class, containing methods such as ``update``, ``array_push``, ``array_pull``.
- ``task_submit_to_db(queue_name: str, task_data: TaskData, weight: int = DefaultValues.TASK.WEIGHT) -> str``: Submits the task to the database (persistence only, no message queue distribution), returns the unique ID of the submitted task.
- ``task_submit_to_db_and_mq(queue_name: str, task_data: TaskData, weight: int = DefaultValues.TASK.WEIGHT) -> str``: Submits the task to the database and distributes it to RabbitMQ (triggers execution), returns the unique task ID.
- ``subtask_batch_create(source_task_id: str, subtask_queue: str, subtask_list: List[TaskData]) -> List[str]``: Batch creates subtasks and saves them to the database (linked to the parent task), returns a list of subtask IDs.

8.10 ``interface/scheduler.py``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ``add_schedule_job(job_id: str, cron_expression: str, function: Callable, timezone: str = "UTC", arguments: Optional[List] = None, keyword_arguments: Optional[Dict] = None, allowed_ips: Optional[List[str]] = None, execution_type: str = "thread") -> bool``: Schedules a job in the distributed scheduler, returns a boolean indicating success.
- ``remove_scheduled_job(job_id: str) -> bool``: Removes a scheduled job from the distributed scheduler, returns a boolean indicating success.
- ``start_scheduler() -> None``: Starts the distributed scheduler.
- ``stop_scheduler() -> None``: Stops the distributed scheduler.
