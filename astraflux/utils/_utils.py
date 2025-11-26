# -*- encoding: utf-8 -*-
import base64
import hashlib

import pytz
import socket
import datetime

from astraflux.definitions.constants import *
from astraflux.interface.definitions import get_current_dir


def _get_default_params(fmt, timezone):
    """
    Get default format and timezone if the input parameters are not provided.

    Args:
        fmt (str or bool): The format of the time string. If False, use the default format.
        timezone (str or bool): The timezone. If False, use the default timezone.

    Returns:
        tuple: A tuple containing the format and timezone.
    """
    if fmt is False:
        fmt = DefaultValues.TIME.TIME_FMT

    if timezone is False:
        timezone = DefaultValues.TIME.TIMEZONE

    return fmt, timezone


def get_date_time_obj(data_str: str, fmt=False, timezone=False):
    """
    Specify the timezone and format, and return a time object.

    Args:
        data_str (str): The time string to be converted.
        fmt (str or bool): The format of the time string. If False, use the default format.
        timezone (str or bool): The timezone. If False, use the default timezone.

    Returns:
        datetime.datetime: A datetime object representing the converted time.
    """
    fmt, timezone = _get_default_params(fmt, timezone)
    target_timezone = pytz.timezone(timezone)
    current_time = datetime.datetime.strptime(data_str, fmt)
    converted_time = current_time.astimezone(target_timezone)
    return converted_time


def format_converted_time(data_str: str, fmt=False, timezone=False, r_fmt=False):
    """
    Format a time string according to the specified format and timezone.

    Args:
        data_str (str): The time string to be formatted.
        fmt (str or bool): The input format of the time string. If False, use the default format.
        timezone (str or bool): The timezone. If False, use the default timezone.
        r_fmt (str or bool): The output format of the time string. If False, use the input format.

    Returns:
        str: A formatted time string.
    """
    fmt, timezone = _get_default_params(fmt, timezone)
    if r_fmt is False:
        r_fmt = fmt

    current_time = datetime.datetime.strptime(data_str, fmt)
    target_timezone = pytz.timezone(timezone)
    converted_time = current_time.astimezone(target_timezone)

    return converted_time.strftime(r_fmt)


def get_converted_time(fmt=False, timezone=False):
    """
    Specify timezone and format, return the current time.

    Args:
        fmt (str or bool): The format of the time string. If False, use the default format.
        timezone (str or bool): The timezone. If False, use the default timezone.

    Returns:
        str: A string representing the current time in the specified format and timezone.
    """
    fmt, timezone = _get_default_params(fmt, timezone)
    current_time = datetime.datetime.now()
    target_timezone = pytz.timezone(timezone)
    converted_time = current_time.astimezone(target_timezone)

    return converted_time.strftime(fmt)


def convert_timestamp_to_timezone(timestamp, fmt=False, timezone=False):
    """
    Convert a timestamp to a time string in the specified timezone and format.

    Args:
        timestamp (float): The timestamp to be converted.
        fmt (str or bool): The format of the time string. If False, use the default format.
        timezone (str or bool): The timezone. If False, use the default timezone.

    Returns:
        str: A string representing the converted time in the specified format and timezone.
    """
    fmt, timezone = _get_default_params(fmt, timezone)
    datetime_utc = datetime.datetime.utcfromtimestamp(timestamp)
    timezone_obj = pytz.timezone(timezone)
    datetime_timezone = datetime_utc.replace(tzinfo=pytz.utc).astimezone(timezone_obj)
    return datetime_timezone.strftime(fmt)


def get_converted_timestamp(date_string: str, fmt=False, timezone=False):
    """
    Convert a time string to a timestamp in the specified timezone and format.

    Args:
        date_string (str): The time string to be converted.
        fmt (str or bool): The format of the time string. If False, use the default format.
        timezone (str or bool): The timezone. If False, use the default timezone.

    Returns:
        float: A timestamp representing the converted time.
    """
    fmt, timezone = _get_default_params(fmt, timezone)
    dt = datetime.datetime.strptime(date_string, fmt)
    target_tz = pytz.timezone(timezone)
    converted_dt = dt.astimezone(target_tz).replace(tzinfo=None)
    return converted_dt.timestamp()


def convert_timestamp_to_timezone_str(timestamp, timezone=False, fmt=False):
    """
    Convert a timestamp to a time string.
    Args:
        timestamp (int): The timestamp to be converted.
        timezone (str or bool): The timezone. If False, use the default timezone.
        fmt (str or bool): The format of the time string. If False, use the default format.
    Returns:
        str: A string representing the converted time in the specified format and timezone.
    """
    fmt, timezone = _get_default_params(fmt=fmt, timezone=timezone)
    datetime_utc = datetime.datetime.utcfromtimestamp(timestamp)
    timezone_obj = pytz.timezone(timezone)
    datetime_timezone = datetime_utc.replace(tzinfo=pytz.utc).astimezone(timezone_obj)
    return datetime_timezone.strftime(fmt)


def get_ipaddr() -> str:
    """
    Retrieves the IP address of the current machine by establishing a UDP connection
    to the specified IP and port.

    Returns:
        str: The IP address of the current machine.
    """
    socket_tools = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_tools.connect((DefaultValues.SOCKET.BIND_IP, DefaultValues.SOCKET.BIND_PORT))
    return socket_tools.getsockname()[0]


def get_devices_id():
    """
    Get Devices ID
    """
    ipaddr = get_ipaddr()
    current_dir = get_current_dir()
    token_str = f'{ipaddr}.{current_dir}'
    hash_object = hashlib.sha256(token_str.encode('utf-8'))
    hash_bytes = hash_object.digest()
    encoded_hash = base64.b64encode(hash_bytes)
    return encoded_hash.decode('utf-8')


def register():
    from astraflux.interface import utils
    utils.get_date_time_obj = get_date_time_obj
    utils.format_converted_time = format_converted_time
    utils.get_converted_time = get_converted_time
    utils.convert_timestamp_to_timezone = convert_timestamp_to_timezone
    utils.convert_timestamp_to_timezone_str = convert_timestamp_to_timezone_str
    utils.get_ipaddr = get_ipaddr
    utils.get_devices_id = get_devices_id

    if REPLACE_SYS_MODULE:
        import sys
        sys.modules['astraflux.interface.utils'] = utils
