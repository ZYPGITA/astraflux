# -*- encoding: utf-8 -*-
import socket

from astraflux.settings.keys import *


def get_ipaddr() -> str:
    """
    Retrieves the IP address of the current machine by establishing a UDP connection
    to the specified IP and port.

    Returns:
        str: The IP address of the current machine.
    """
    socket_tools = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_tools.connect((SOCKET.SOCKET_BIND_IP, SOCKET.SOCKET_BIND_PORT))
    return socket_tools.getsockname()[0]


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
    if ip_addr is None:
        ip_addr = get_ipaddr()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip_addr, int(port)))
        s.shutdown(SOCKET.SOCKET_SHUTDOWN_SLEEP)
        return False
    except IOError:
        return True


def register():
    from astraflux.interface import network
    network.get_ipaddr = get_ipaddr
    network.is_port_open = is_port_open

    import sys
    sys.modules['astraflux.interface.network'] = network
