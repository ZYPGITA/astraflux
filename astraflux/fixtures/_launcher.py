# -*- encoding: utf-8 -*-

import sys
import time
import psutil
import logging
import subprocess
import gradio as gr
from pathlib import Path
from typing import List, Callable

from astraflux.ui.app import WebApp

from astraflux.core import global_manager
from astraflux.definitions.constants import *
from astraflux.interface.executor import thread_executor


def run_web_app(logger, config):
    """
    Run web app
    """

    WebApp(logger=logger, config=config).web_launch()


class LauncherManager:

    def __init__(self, config: dict, schedule, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.schedule = schedule

        self.yaml_file = config[PROJECT.CONFIG_PATH.value]
        self.current_dir = config[PROJECT.CURRENT_DIR.value]

        self.python_process_name = 'python'
        self.pyexe = sys.executable if 'python' in sys.executable else 'python3'

        self.services = []
        self.run_process = []

    def _terminate_existing_process(self, script_path: Path, target_path: Path):
        """
        Terminate existing processes running the same script to prevent duplicates.

        This method identifies and kills processes that are running the same
        service or worker script to ensure clean startup without conflicts.

        Args:
            script_path: Path to the framework launcher script
            target_path: Path to the target service/worker class file

        Note:
            Uses psutil to safely identify and terminate matching processes
        """
        for process in psutil.process_iter(['name', 'cmdline']):
            try:
                process_name = process.name()
                command_line = process.cmdline()

                # Check if this is a Python process
                if self.python_process_name in process_name:
                    script_running = False
                    target_running = False

                    # Check command line arguments for script and target paths
                    for argument in command_line:
                        argument_path = Path(argument).as_posix()
                        if script_path.as_posix() in argument_path:
                            script_running = True
                        if target_path.as_posix() in argument_path:
                            target_running = True

                    # Terminate if both script and target are running
                    if script_running and target_running:
                        process.kill()
                        time.sleep(0.1)  # Brief pause to ensure process termination
                        break

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Continue with other processes if current one is inaccessible
                continue

    def _launch_service_component(self, launcher_module, class_path: Path | str) -> int:
        """
        Launch a service or worker component as a separate process.

        Args:
            launcher_module: Type of component to launch ('service' or 'worker')
            class_path: Path to the service/worker class file

        Returns:
            Process ID of the launched component

        Raises:
            ImportError: If the required launcher module cannot be imported
            subprocess.SubprocessError: If process launch fails
        """
        launcher_script = Path(launcher_module.__file__).resolve()

        # Ensure no existing processes are running
        self._terminate_existing_process(launcher_script, class_path)

        # Build command for subprocess execution
        command = [
            self.pyexe,
            launcher_script,
            '--yaml_file', self.yaml_file,
            '--class_path', class_path.as_posix(),
            '--current_dir', self.current_dir
        ]

        # Launch process and return PID
        process = subprocess.Popen(command)
        self.run_process.append(process.pid)
        return process.pid

    def launch_register(self, services: List[Callable]):
        """
        Register services to be managed by the framework.

        Args:
            services: List of service classes or modules to register

        """
        self.services.extend(services)

    def launch_start(self, run_app: bool = True, scheduled: bool = True):
        """
        Initialize and launch all registered services with their associated worker components.

        This method orchestrates the startup process for all services registered in the system.
        For each service, it launches two distinct components:
        1. A service component (RPC server) for handling remote procedure calls and API requests
        2. A worker component (task processor) for executing background tasks and job processing

        After launching all service/worker pairs, the method configures and starts essential
        system-level background jobs:
        - TaskScheduler: Distributes tasks across available workers (runs every 10 seconds)
        - SystemMonitoring: Monitors system health and performance (runs every 30 seconds)

        These background jobs run with different execution modes to ensure proper coordination
        in distributed environments.

        Raises:
            RuntimeError: If any service or worker fails to start properly
            ImportError: If required launcher modules cannot be imported
            FileNotFoundError: If service module file cannot be located

        Note:
            - Service and worker components are launched as separate processes
            - Both components share the same service class module but operate in different modes
            - The scheduler uses distributed_unique mode for task scheduling to ensure
              only one scheduler runs across the entire cluster
            - Monitoring runs in ip_unique mode to ensure one monitor per IP address

        """
        from astraflux.launchers import service_launcher
        from astraflux.launchers import worker_launcher

        for service in self.services:
            # Resolve absolute path to the service module file
            service_class_path = Path(service.__file__).resolve()

            # Launch service component (RPC server)
            service_pid = self._launch_service_component(service_launcher, service_class_path)
            self.logger.info(f"Service started with PID: {service_pid}")

            # Launch worker component (task processor)
            worker_pid = self._launch_service_component(worker_launcher, service_class_path)
            self.logger.info(f"Worker started with PID: {worker_pid}")

        if scheduled:
            # Import system-level workflow components
            from astraflux.workflows.task_distribution import TaskScheduler
            from astraflux.workflows.monitoring import SystemMonitoring

            # Configure and schedule the TaskScheduler job
            # This job runs every 10 seconds and is responsible for distributing tasks
            # across available workers in a distributed environment
            self.schedule.add_scheduled_job(
                job_id='TaskScheduler',
                cron_expression='*/10 * * * * *',  # Every 10 seconds
                execution_type='thread',  # Execute in a separate thread
                function=TaskScheduler().execute,  # Function to execute
                execution_mode='distributed_unique'  # Ensure only one instance runs in the cluster
            )

            # Configure and schedule the SystemMonitoring job
            # This job runs every 30 seconds and monitors system health and performance
            self.schedule.add_scheduled_job(
                job_id='SystemMonitoring',
                cron_expression='*/30 * * * * *',  # Every 30 seconds
                execution_type='thread',  # Execute in a separate thread
                function=SystemMonitoring().run,  # Function to execute
                execution_mode='ip_unique'  # Ensure one instance per IP address
            )

            # Start the scheduler to begin executing scheduled jobs
            self.schedule.start_scheduler()

        if run_app:
            t = thread_executor()
            t.submit(func=run_web_app, logger=self.logger, config=self.config)
            t.start()

    def kill(self):
        """
        Terminate all running service and worker processes forcefully.

        This method sends a SIGKILL signal (signal 9) to all process IDs stored in
        the `self.run_process` list, which contains the PIDs of all service and
        worker processes started by this manager. The SIGKILL signal immediately
        terminates the target processes without allowing them to perform cleanup
        operations.

        WARNING:
            Using SIGKILL is a forceful termination method that can lead to:
            - Resource leaks (unclosed files, sockets, database connections)
            - Data corruption if processes were in the middle of write operations
            - Inconsistent system state
            Use this method only when graceful shutdown is not possible or when
            immediate termination is required.

        Usage:
            This method is typically called during:
            - System shutdown procedures
            - Emergency termination scenarios
            - Process cleanup during error recovery
            - Testing and development environment resets

        Note:
            - The method uses `os.system` to execute the kill command, which may
              have security implications in production environments
            - Alternative approaches using `os.kill` or `subprocess` modules may
              provide better control and security
            - Ensure `self.run_process` contains valid process IDs before calling
            - This method does not validate if the PIDs are still running

        Raises:
            OSError: If the underlying system call to kill processes fails
            PermissionError: If the process lacks permissions to terminate target processes
            AttributeError: If `self.run_process` is not properly initialized

        """
        import os
        # Construct and execute kill command for all stored process IDs
        # Using SIGKILL (signal 9) ensures immediate termination
        os.system(f'kill -9 {" ".join(self.run_process)}')


@global_manager.register_fixture(name="fixture_launcher", scope=Scope.GLOBAL)
def _launcher(fixture_config, fixture_logger, fixture_schedule):
    """Register LauncherManager fixture"""
    _config = fixture_config
    _logger = fixture_logger.get_logger(PROJECT.NAME.value, 'LauncherManager')

    _launcher_manager = LauncherManager(
        config=_config,
        schedule=fixture_schedule,
        logger=_logger,
    )

    yield _launcher_manager

    _launcher_manager.kill()
