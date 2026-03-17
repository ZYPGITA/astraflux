AstraFlux Framework User Guide
==============================

Overview
--------
AstraFlux is a lightweight distributed service management framework with core capabilities including:
- Simplifying the definition, registration, and startup process of distributed RPC services;
- Providing scheduling and execution capabilities for asynchronous Worker tasks;
- Integrating MongoDB/Redis/RabbitMQ middleware to unify data storage, caching, and message communication capabilities;
- Built-in task scheduling, log management, process monitoring and other basic capabilities to reduce the cost of distributed service development.

Configuration Instructions
--------------------------
2.1 Configuration File Structure (config.yaml)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The framework centrally manages core configurations such as middleware connections and logs through ``config.yaml``, with the following example:

.. code-block:: yaml

    # MongoDB Configuration
    mongodb:
      host: 127.0.0.1
      port: 27017
      db: astraflux
      username: scheduleAdmin
      password: scheduleAdminPassword

    # Redis Configuration
    redis:
      host: 127.0.0.1
      port: 6379
      password: scheduleAdminPassword
      db_index: 8

    # RabbitMQ Configuration
    rabbitmq:
      host: 127.0.0.1
      port: 5672
      username: scheduleAdmin
      password: scheduleAdminPassword

    # Logger Configuration
    logger:
      path: logs  # Log storage directory
      level: INFO # Log level (DEBUG/INFO/WARN/ERROR)

    # Web Manage Configuration
    web:
      prot: 7860
      username: scheduleAdmin
      password: scheduleAdminPassword

Framework Usage Steps
---------------------
3.1 Environment Preparation
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Ensure the core framework dependencies are installed:

.. code-block:: bash

    pip install astraflux

3.2 Recommended Project Directory Structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

    your_project/
    ├── config.yaml       # Framework configuration file
    ├── server/           # Service implementation directory
    │   ├── __init__.py
    │   └── test_server.py # Custom RPC/Worker service
    └── main.py           # Framework startup entry

3.3 Define Custom Services
~~~~~~~~~~~~~~~~~~~~~~~~~~
You need to implement RPC services (handling remote calls) and Worker services (handling asynchronous tasks) separately, as shown in the example below (``server/test_server.py``):

.. code-block:: python

    from astraflux import ServiceConstructor, WorkerConstructor, rpc_decorator
    import time

    # 1. Define RPC Service (handling remote calls)
    class TestRpcService(ServiceConstructor):
        # Must define service name for registration and identification
        service_name = "test_server"

        # Mark RPC methods with @rpc_decorator to support external calls
        @rpc_decorator
        def get_version(self):
            """Example: Return service version"""
            return {"code": 200, "data": "test_server v1.0"}

        @rpc_decorator
        def calculate(self, a, b):
            """Example: Receive parameters and return calculation results"""
            return {"code": 200, "data": a + b}

    # 2. Define Worker Service (handling asynchronous tasks)
    class TestWorkerService(WorkerConstructor):
        # Must define Worker name, consistent with RPC service name
        worker_name = "test_server"

        def run(self, data):
            """
            Must implement the run method as the task execution entry
            :param data: Task input parameters (dictionary format)
            """
            self.logger.info(f"Start executing task with parameters: {data}")
            # Simulate task execution
            time.sleep(2)
            self.logger.info(f"Task execution completed, Task ID: {data.get('task_id')}")
            return {"status": "success"}

3.4 Framework Initialization and Service Registration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Complete framework initialization, service registration and startup in the startup entry file (``main.py``):

.. code-block:: python

    # -*- coding: utf-8 -*-
    import os
    from astraflux import AstraFlux, launch_register, launch_start
    # Import custom services
    from server.test_server import TestRpcService, TestWorkerService

    # 1. Get current directory (for locating configuration files)
    current_dir = os.path.dirname(__file__)

    # 2. Initialize framework (load configuration file, singleton mode)
    AstraFlux(
        yaml_path=f"{current_dir}/config.yaml",  # Configuration file path
        current_dir=current_dir                 # Framework working directory
    )

    # 3. Register custom services (RPC+Worker services)
    launch_register(services=[
        TestRpcService,
        TestWorkerService
    ])

    # 4. Start all registered services
    launch_start()

    # Keep main process running
    if __name__ == "__main__":
        while True:
            pass

Core Interface Examples
-----------------------
4.1 RPC Service Call
~~~~~~~~~~~~~~~~~~~~
Call registered RPC services through the framework's built-in ``proxy_call`` interface:

.. code-block:: python

    from astraflux import proxy_call

    # Call get_version method of test_server
    result1 = proxy_call(
        service_name="test_server",  # Target service name
        method_name="get_version"    # Target method name
    )
    print(result1)  # Output: {"code": 200, "data": "test_server v1.0"}

    # Call calculate method of test_server (with parameters)
    result2 = proxy_call(
        service_name="test_server",
        method_name="calculate",
        a=10, b=20  # Method input parameters
    )
    print(result2)  # Output: {"code": 200, "data": 30}

4.2 Submit Worker Asynchronous Tasks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Submit asynchronous tasks to the specified Worker through the ``task_submit`` interface:

.. code-block:: python

    from astraflux import task_submit, subtask_batch_create

    # Submit task to test_server Worker
    task_id = task_submit(
        worker_name="test_server",  # Target Worker name
        data={                      # Task parameters
            "task_id": "task_001",
            "param1": "value1",
            "param2": 123
        }
    )
    print(f"Task submitted successfully, Task ID: {task_id}")

    # Create subtasks, the framework automatically monitors task status
    # and updates the main task after all subtasks are completed
    subtask_batch_create(
        subtask_queue='sub_test_server',
        source_id='task_001',
        subtask_list=[
            {'x': 1, 'y': 2},
            {'x': 2, 'y': 3},
        ]
    )

4.3 Middleware Operation Interfaces
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
4.3.1 MongoDB Operations
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from astraflux import mongodb_find_from_task, mongodb_find_paginated_from_task

    # 1. Query task data
    task_data = mongodb_find_from_task(
        query={"task_id": "task_001"},  # Query conditions
        fields={"_id": 0}    # Return fields
    )

    # Pagination query
    mongodb_find_paginated_from_task(
        query={"task_id": "task_001"},
        fields={},
        limit=100,
        skip=0
    )

4.3.2 Redis Operations
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from astraflux import redis_update_max_process

    redis_update_max_process(
        unique_id='test_server_127.0.0.1',  # Service name_IP
        new_value=10  # Set the maximum number of worker processes for the service on the corresponding IP
    )

4.4 Task Scheduling Interfaces
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from astraflux import add_scheduled_job, start_scheduler

    # Add scheduled task (execute every minute)
    add_scheduled_job(
        job_id="test_job",
        func=lambda: print("Scheduled task executed"),
        trigger="interval",
        minutes=1
    )

    # Start scheduler, no need to start manually when using launch_start
    start_scheduler()

4.5 Log Usage Example
~~~~~~~~~~~~~~~~~~~~~
The framework has a built-in logging module that can be used directly in services:

.. code-block:: python

    from astraflux import logger

    # Global logger usage
    logger.info("Framework started successfully")
    logger.error("Service startup failed", exc_info=True)

    # Worker service built-in logger
    class TestWorkerService(WorkerConstructor):
        worker_name = "test_server"
        def run(self, data):
            self.logger.debug(f"Task parameters: {data}")  # DEBUG level log
            self.logger.warn("Task execution timeout warning")    # WARN level log

4.6 Thread/Process Pool Executor Usage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The framework provides thread and process pool executors with built-in retry mechanisms
for reliable task execution. Process executors are suitable for CPU-bound tasks, while
thread executors are better for I/O-bound operations.

.. code-block:: python

    import time
    from astraflux import process_executor, thread_executor

    def test_func(x):
        """Test function that runs in an infinite loop printing values"""
        while True:
            print(x)
            time.sleep(1)

    if __name__ == '__main__':
        # Important Note for Windows Systems:
        # - Process executor calls must be within __main__ block if not used inside WorkerFunction
        # - Thread executor can be used in WorkerFunction or __main__ block

        # Initialize and use process pool executor
        p = process_executor(max_workers=5, retry_delay=1.0)
        # Submit tasks to process pool
        p.submit(func=test_func, x=1)
        p.submit(func=test_func, x=2)
        # Start process pool executor
        p.start()

        # Initialize and use thread pool executor
        t = thread_executor(max_workers=5, retry_delay=1.0)
        # Submit tasks to thread pool (automatically starts when first task is submitted)
        t.submit(func=test_func, x=3)
        t.submit(func=test_func, x=4)

        # Keep main process running to prevent executor shutdown
        while True:
            pass

    **Executor Configuration Parameters**:
    - ``max_workers``: Maximum number of worker threads/processes (default: 5)
    - ``retry_delay``: Base delay time (in seconds) between retry attempts for failed tasks (default: 1.0)

    **Key Differences Between Executors**:
    1. **Process Executor**:
       - Requires explicit ``start()`` call to begin task execution
       - Must be used within ``__main__`` block on Windows (outside WorkerFunction)
       - Ideal for CPU-bound tasks that benefit from multiple cores
       - Uses inter-process communication with task serialization

    2. **Thread Executor**:
       - Automatically starts when first task is submitted
       - No special execution context requirements
       - Ideal for I/O-bound tasks with frequent waiting operations
       - Lower overhead compared to process executor

    **Executor Retry Mechanism**:
    Both executors automatically retry failed tasks with exponential backoff:
    - Retry delay increases with each attempt (retry_delay * retry_count)
    - Maximum retry attempts default to 3 (configurable per task)
    - Failed tasks after max retries are tracked and can be retrieved via ``get_failed_tasks()``

For more interface usage, please refer to astraflux.interface.
