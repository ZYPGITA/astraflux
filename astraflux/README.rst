AstraFlux User Documentation
============================

.. code-block:: bash

    AstraFlux enables rapid setup of distributed task systems with minimal configuration. Key features:
    1.Asynchronous/scheduled tasks
    2.Distributed task processing
    3.Service registration, monitoring, dynamic configuration injection, load balancing

Framework Initialization
========================

.. code-block:: bash

    1. Create File config.yaml

    Mongodb:
      host: 127.0.0.1
      port: 27017
      db: astraflux
      username: scheduleAdmin
      password: scheduleAdminPassword

    Redis:
      host: 127.0.0.1
      port: 6379
      password: scheduleAdminPassword

    RabbitMQ:
      host: 127.0.0.1
      port: 5672
      username: scheduleAdmin
      password: scheduleAdminPassword

    logger:
      level: INFO

    2. Initialize in main.py

    import os
    os_dir = os.path.dirname(__file__)
    af = AstraFlux('config.yaml', os_dir)


Service Registration
====================

1. Create service file (e.g., test_server.py):

.. code-block:: bash

    # -*- coding: utf-8 -*-

    from nexusflow import *


    class RpcFunction(ServiceConstructor):
        service_name = 'test_server'

        """All functions are automatically proxied for RPC calls"""

        def get_service_name(self):
            return {"service_version": self.service_version}

        def test_func(self, **args):
            return args

    class WorkerFunction(WorkerConstructor):
        worker_name = 'test_server'

        def run(self, data):
            self.loguru.info(data)
            """
            Executed when new tasks appear in worker_name queue.
            Implement business logic here. `data` contains all task data.
            """

2. Register the service in main.py

.. code-block:: bash

    import test_server
    af.registry(services=[test_server])

    af.start()


Scheduled/Asynchronous Tasks
============================

.. code-block:: bash

    from nexusflow.interface import *

    # Generate Snowflake ID
    _id = snowflake_id()

    # Create task
    message = {'task_id': 'test_003', 'status': 'wait', 'name': 'xxxx'}
    task_submit_databases(queue='test_server', message=message)

    # Create subtasks (automatic status updates)
    subtask_create(
        source_task_id='test_003',
        subtask_queue='test_server_sub',
        subtasks=[{
            'task_id': snowflake_id(),
            'name': 'subtask1',
        }]
    )

    # Stop task
    task_stop(task_id='test_003')

    # MongoDB interfaces
    mongodb_task()     # Task operations
    mongodb_node()     # Node operations
    mongodb_services() # Service operations

    # Redis interfaces
    redis_task()
    redis_services()

    # RPC service call (auto load-balanced)
    result = proxy_call(
        service_name='test_server',
        method_name='test_func',
        a=1, b=2  # Function arguments
    )

Function Reference
==================


.. code-block:: bash

    from nexusflow.interface import *

    # Generate Snowflake ID
    _id = snowflake_id()

    # Create task
    message = {'task_id': 'test_003', 'status': 'wait', 'name': 'xxxx'}
    task_submit_databases(queue='test_server', message=message)

    # Create subtasks (automatic status updates)
    subtask_create(
        source_task_id='test_003',
        subtask_queue='test_server_sub',
        subtasks=[{
            'task_id': snowflake_id(),
            'name': 'subtask1',
        }]
    )

    # Stop task
    task_stop(task_id='test_003')

    # MongoDB interfaces
    mongodb_task()     # Task operations
    mongodb_node()     # Node operations
    mongodb_services() # Service operations

    # Redis interfaces
    redis_task()
    redis_services()

    # RPC service call (auto load-balanced)
    result = proxy_call(
        service_name='test_server',
        method_name='test_func',
        a=1, b=2  # Function arguments
    )
