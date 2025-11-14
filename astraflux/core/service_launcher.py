# -*- encoding: utf-8 -*-

import os
import sys
import argparse


class ServiceComponentLauncher:
    """
    Launcher for RPC service components in the distributed framework.

    Handles the complete lifecycle of service components including:
    - Dynamic class loading and configuration
    - Service registration in the service discovery system
    - RPC server startup and request handling
    """

    def __init__(self, class_path: str):
        """
        Initialize the service launcher.

        Args:
            class_path: Path to the service class definition file
        """
        self.class_path = class_path

    def launch_service(self):
        """
        Launch and register the RPC service component.

        This method:
        1. Builds the service component using ServiceBuilder
        2. Registers the service in the service discovery database
        3. Starts the RPC server to handle incoming requests
        """
        # Build service component with dynamic class loading
        service_builder = Build(
            class_path=self.class_path,
            component_type='service',
            constructor=ServiceConstructor
        )
        service_component = service_builder.build_component()

        # Prepare service registration data
        service_registration_data = self._prepare_service_data(service_component)

        # Register service in the service discovery system
        self._register_service_in_discovery(service_component, service_registration_data)

        # Log successful service startup
        service_component.logger.info(f'Service component started: {service_registration_data}')

        # Start RPC server to handle incoming requests
        self._start_rpc_server(service_component)

    @staticmethod
    def _prepare_service_data(service_component) -> dict:
        """
        Prepare service data for registration in discovery system.

        Args:
            service_component: Configured service component instance

        Returns:
            Dictionary containing service metadata for registration
        """
        return {
            DEFINITIONS.BUILD.NAME: service_component.name,
            DEFINITIONS.BUILD.SERVICE_IPADDR: service_component.ipaddr,
            DEFINITIONS.BUILD.SERVICE_NAME: service_component.service_name,
            DEFINITIONS.BUILD.SERVICE_VERSION: service_component.version,
            DEFINITIONS.BUILD.SERVICE_PID: os.getpid(),
            DEFINITIONS.BUILD.SERVICE_FUNCTIONS: service_component.functions,

            # Initialize worker attributes for service discovery
            DEFINITIONS.BUILD.WORKER_IPADDR: service_component.ipaddr,
            DEFINITIONS.BUILD.WORKER_NAME: service_component.service_name
        }

    @staticmethod
    def _register_service_in_discovery(service_component, service_data: dict):
        """
        Register service in the service discovery database.

        Args:
            service_component: Service component instance
            service_data: Service metadata for registration
        """
        service_collector().update(
            query={
                DEFINITIONS.BUILD.SERVICE_IPADDR: service_component.ipaddr,
                DEFINITIONS.BUILD.SERVICE_NAME: service_component.service_name
            },
            data=service_data,
            upsert=True  # Create if doesn't exist
        )

    @staticmethod
    def _start_rpc_server(service_component):
        """
        Start the RPC server to handle remote procedure calls.

        Args:
            service_component: Service component instance to handle RPC requests
        """
        service_running(service_cls=service_component)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Distributed Service Component Launcher")

    # Define command line arguments
    parser.add_argument("--yaml_file", type=str, required=True,
                        help="Path to YAML configuration file")
    parser.add_argument("--class_path", type=str, required=True,
                        help="Path to service class definition file")
    parser.add_argument("--root_path", type=str, required=True,
                        help="Root path of the application")
    parser.add_argument("--current_dir", type=str, required=True,
                        help="Current working directory")

    # Parse arguments
    args = parser.parse_args()

    # Add current directory to Python path for module discovery
    sys.path.append(args.current_dir)
    sys.path.append(args.root_path)

    from astraflux.inject import inject_init
    from astraflux.definitions.constants import *
    from astraflux.interface.core import ServiceConstructor, init_global_vars
    from astraflux.interface.rpc import service_running
    from astraflux.interface.data_access import service_collector

    from astraflux.core.build import Build

    # Initialize dependency injection system
    inject_init(root_path=args.root_path)

    # Initialize global variables and configuration
    init_global_vars(
        yaml_file=args.yaml_file,
        current_dir=args.current_dir,
        root_path=args.root_path
    )

    # Launch the service component
    ServiceComponentLauncher(class_path=args.class_path).launch_service()
