# -*- encoding: utf-8 -*-


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
    return get_date_time_obj(data_str, fmt, timezone)


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
    return format_converted_time(data_str, fmt, timezone, r_fmt)


def get_converted_time(fmt=False, timezone=False):
    """
    Specify timezone and format, return the current time.

    Args:
        fmt (str or bool): The format of the time string. If False, use the default format.
        timezone (str or bool): The timezone. If False, use the default timezone.

    Returns:
        str: A string representing the current time in the specified format and timezone.
    """
    return get_converted_time(fmt, timezone)


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
    return convert_timestamp_to_timezone(timestamp, fmt, timezone)


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
    return get_converted_timestamp(date_string, fmt, timezone)


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
    return convert_timestamp_to_timezone_str(timestamp, timezone, fmt)


def get_ipaddr() -> str:
    """
    Retrieves the IP address of the current machine by establishing a UDP connection
    to the specified IP and port.

    Returns:
        str: The IP address of the current machine.
    """
    return get_ipaddr()
