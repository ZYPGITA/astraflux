# -*- encoding: utf-8 -*-

import sys
import time

import psutil
import subprocess
from pathlib import Path
from typing import List, Callable

from astraflux.definitions.constants import REPLACE_SYS_MODULE
from astraflux.interface.definitions import get_current_dir, get_root_path
from astraflux.interface.scheduler import add_schedule_job, start_scheduler
from astraflux.interface.logger import get_logger

from astraflux.workflows.task_distribution import TaskScheduler

# Global constants
_PYTHON_NAME = 'python'
_PYEXEC = sys.executable if 'python' in sys.executable else 'python3'

# Global service registry
_REGISTERED_SERVICES = []


class ProcessManager:
    """
    Manages process lifecycle for service and worker components.

    Provides functionality to terminate existing processes and launch
    new service/worker instances with proper isolation.
    """

    @staticmethod
    def terminate_existing_process(script_path: Path, target_path: Path):
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
                if _PYTHON_NAME in process_name:
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

    @staticmethod
    def launch_service_component(component_type: str, class_path: Path, yaml_config: str) -> int:
        """
        Launch a service or worker component as a separate process.

        Args:
            component_type: Type of component to launch ('service' or 'worker')
            class_path: Path to the service/worker class file
            yaml_config: Path to the YAML configuration file

        Returns:
            Process ID of the launched component

        Raises:
            ImportError: If the required launcher module cannot be imported
            subprocess.SubprocessError: If process launch fails
        """
        # Import appropriate launcher based on component type
        if component_type == 'service':
            from . import service_launcher as launcher_module
        else:
            from . import worker_launcher as launcher_module

        launcher_script = Path(launcher_module.__file__).resolve()

        # Ensure no existing processes are running
        ProcessManager.terminate_existing_process(launcher_script, class_path)

        # Build command for subprocess execution
        command = [
            _PYEXEC,
            launcher_script,
            '--yaml_file', yaml_config,
            '--class_path', class_path.as_posix(),
            '--root_path', get_root_path(),
            '--current_dir', get_current_dir()
        ]

        # Launch process and return PID
        process = subprocess.Popen(command)
        return process.pid


class ServiceRegistry:
    """
    Manages registration and lifecycle of distributed services.

    Provides a central registry for services and coordinates
    the startup of service and worker components.
    """

    @staticmethod
    def register_services(services: List[Callable]):
        """
        Register services to be managed by the framework.

        Args:
            services: List of service classes or modules to register

        """
        _REGISTERED_SERVICES.extend(services)

    @staticmethod
    def start_all_services(yaml_config: str):
        """
        Start all registered services and their worker components.

        This method launches each registered service as both a service
        (for RPC calls) and a worker (for task processing).

        Args:
            yaml_config: Path to the YAML configuration file

        Raises:
            RuntimeError: If service startup fails
        """
        for service in _REGISTERED_SERVICES:
            service_class_path = Path(service.__file__).resolve()

            # Launch service component (RPC server)
            service_pid = ProcessManager.launch_service_component(
                'service', service_class_path, yaml_config
            )
            get_logger().info(f"Service started with PID: {service_pid}")

            # Launch worker component (task processor)
            worker_pid = ProcessManager.launch_service_component(
                'worker', service_class_path, yaml_config
            )
            get_logger().info(f"Worker started with PID: {worker_pid}")

    @staticmethod
    def start_scheduler():
        add_schedule_job(
            job_id='TaskScheduler001',
            cron_expression='*/10 * * * * *',
            execution_type='thread',
            function=TaskScheduler().execute,
        )

        start_scheduler()


# Backward compatibility functions
def services_registry(services: List[Callable]):
    """Legacy function for service registration."""
    ServiceRegistry.register_services(services)


def services_start(yaml_config: str):
    """Legacy function for starting all services."""
    ServiceRegistry.start_all_services(yaml_config)
    ServiceRegistry.start_scheduler()


def register():
    from astraflux.interface import core
    core.services_registry = services_registry
    core.services_start = services_start

    if REPLACE_SYS_MODULE:
        import sys
        sys.modules['astraflux.interface.core'] = core
