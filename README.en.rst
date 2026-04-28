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

Astra Agent Usage
-----------------

5.1 Overview
~~~~~~~~~~~~

``astra_agents`` is a built-in AI agent module of the AstraFlux framework. It provides
two agent implementations:

- **AstraNativeAgent** — A native AI agent that uses the OpenAI SDK directly,
  supports tool registration, conversation history management, and automatic tool
  call handling without relying on third-party agent frameworks.

- **OpenClawChat** — A client that communicates with an `OpenClaw <https://github.com/openclaw/openclaw>`__
  AI gateway, managing system prompts, skill learning tasks, and streaming chat
  interactions.

Both agents share a common skill system located at ``astraflux/astra_agents/skill/``.
The framework also supports expandable skills (user-defined skill plugins).

5.2 Skill System
~~~~~~~~~~~~~~~~

The agent skill system is a plug-in system that provides AI agents with the ability
to call various local and external tools. The system has two types of skills:

.. code-block:: text

    astraflux/astra_agents/skill/          # Built-in system skills (read-only)
        dirs/                              # Directory/file system operations
        exec/                              # Shell command execution (cross-platform)
        files/                             # File read/write (multi-format)
        Internet/                          # Web search, fetch, download, URL check

    <project_dir>/<expand_skill_directory>/  # User-defined expandable skills (read-only)

**Built-in Skills:**

.. list-table::
    :widths: 15 30 55

    * - **Skill**
      - **Tools**
      - **Description**
    * - ``dirs``
      - ``create_directory``, ``remove_directory``, ``list_directory``, ``rename_directory``, ``get_directory_info``, ``set_permissions``, ``get_permissions``
      - Create, remove, list, rename directories; query and set file/directory permission information.
    * - ``exec``
      - ``execute``
      - Cross-platform shell command execution (Windows/Linux/macOS/WSL). Supports various shells (cmd, PowerShell, bash, zsh), environment variable injection, timeout, and working directory settings.
    * - ``files``
      - ``read_file``, ``write_file``, ``show_format_example``
      - Unified file reading and writing for multiple formats: txt, json, csv, xml, yaml, toml, ini, env, excel. Automatically detects format by file extension or explicit specification.
    * - ``Internet``
      - ``search_web``, ``fetch_webpage``, ``download_file``, ``check_url``
      - Search (supports DuckDuckGo, Google, Baidu, Yandex, Yahoo, Bing), fetch web page content as markdown/text, download files, check URL accessibility.

5.3 Configuration
~~~~~~~~~~~~~~~~~

The agent is configured through the ``config.yaml`` file in the AstraFlux configuration:

.. code-block:: yaml

    # Example config.yaml entries for astra_agents

    openai:  # Configuration for AstraNativeAgent
      model_api:
        server: https://api.openai.com/v1
        apikey: your-api-key-here
        name: gpt-4o  # or gpt-4o-mini, deepseek-chat, etc.
      temporary_directory: temporary_directory   # Writable directory for agent
      expand_skill_directory: expand_skill       # User skill plugin directory

    openclaw:  # Configuration for OpenClawChat
      server: http://localhost:8120
      token: your-openclaw-token
      session_key: your-session-key
      temporary_directory: temporary_directory   # Writable directory for agent
      expand_skill_directory: expand_skill       # User skill plugin directory

**Configuration fields:**

- ``server`` — API server URL (OpenAI-compatible API or OpenClaw gateway)
- ``apikey`` / ``token`` — API authentication
- ``name`` — Model name (e.g., ``gpt-4o``, ``deepseek-chat``)
- ``temporary_directory`` — The only writable directory the agent can use
- ``expand_skill_directory`` — Directory for user-defined skill plugins

5.4 AstraNativeAgent Basic Usage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # -*- coding: utf-8 -*-
    import os
    from astraflux import *

    # 1. Initialize AstraFlux framework
    current_dir = os.path.dirname(__file__)
    AstraFlux(
        yaml_path=f"{current_dir}/config.yaml",
        current_dir=current_dir
    )

    # 2. Chat with the agent (async)
    import asyncio

    def backcall(data):
        print(data)

    message = 'Hello !'
    asyncio.run(o.chat(message, backcall))

5.5 OpenClawChat Basic Usage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # -*- coding: utf-8 -*-
    import os
    from astraflux import AstraFlux

    # 1. Initialize AstraFlux framework
    current_dir = os.path.dirname(__file__)
    AstraFlux(
        yaml_path=f"{current_dir}/config.yaml",
        current_dir=current_dir
    )

    # 2. Send a message (streaming)
    response_gen = send_message_to_openclaw(
        user_message="List files in the current directory"
    )
    for chunk in response_gen:
        print(chunk, end="", flush=True)

**Key Methods:**

- ``send_message_to_openclaw(user_message, user_id, prompt)`` — Send a message (returns streaming generator)
- ``stream_chat(payload)`` — Low-level streaming API call
- ``initialize_ai()`` — Called automatically on construction; sends system learning tasks

5.6 Custom Tool Registration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can register custom Python functions as tools for ``AstraNativeAgent``:

.. code-block:: python

    from astraflux.astra_agents.astra_agent import AstraAgentApi

    # After creating the agent instance
    @agent.register_tool
    def get_weather(city: str) -> str:
        """Get current weather for a city."""
        return f"Weather in {city}: Sunny, 22C"

    # Or call directly
    def my_tool(name: str, count: int = 10) -> str:
        """My custom tool description."""
        return f"Processed {count} items for {name}"

    agent.register_tool(my_tool, name="process_items", description="Process items for a user")

The agent automatically extracts parameter schemas from Python type annotations
and builds OpenAI-compatible tool definitions.

5.7 Expandable Skills
~~~~~~~~~~~~~~~~~~~~~

To create your own skill plugin, follow the built-in skill conventions:

1. Create a subdirectory in the ``expand_skill_directory`` configured in ``config.yaml``
2. Add an ``__init__.py`` containing ``@function_tool``-decorated functions
3. On initialization, the agent automatically scans and registers all ``__init__.py``
   files in the expandable skill directory

.. note:: The ``function_tool`` decorator must be imported from
          ``astraflux.interface.astra_agents`` (or ``agents`` for compatibility
          with the Open AI Agents SDK). The agent uses the ``_is_function_tool``
          attribute to discover tool functions during dynamic import.

For more interface usage, please refer to astraflux.interface.
