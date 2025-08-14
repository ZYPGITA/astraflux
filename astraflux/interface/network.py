# -*- encoding: utf-8 -*-
import sys

__all__ = ['get_ipaddr', 'is_port_open']


def get_ipaddr() -> str:
    """
    Retrieves the IP address of the current machine by establishing a UDP connection
    to the specified IP and port.

    Returns:
        str: The IP address of the current machine.
    """
    return sys.modules[__name__].get_ipaddr()


def is_port_open(port: int, ip_addr: str = None) -> bool:
    """
    Checks if a specified port on a given IP address is open by attempting to establish
    a TCP connection.

    Args:
        ip_addr (str): The IP address to check.
        port (int): The port number to check.

    Returns:
        bool: True if the port is closed, False if the port is open.
    """
    return sys.modules[__name__].is_port_open(port, ip_addr)
