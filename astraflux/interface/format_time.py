# -*- encoding: utf-8 -*-
from astraflux.inject import inject_implementation

__all__ = [
    "get_date_time_obj",
    "format_converted_time",
    "get_converted_time",
    "get_yes_today",
    "get_yesterday_date",
    "convert_timestamp_to_timezone",
    "get_converted_timestamp",
    "get_date_list",
    "get_week_num",
    "get_current_week",
    "is_timestamp_within_days",
    "convert_timestamp_to_timezone_obj",
    "convert_timestamp_to_timezone_str",
    'get_converted_time_float'
]


@inject_implementation()
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


@inject_implementation()
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


@inject_implementation()
def get_converted_time(fmt=False, timezone=False):
    """
    Specify timezone and format, return the current time.

    Args:
        fmt (str or bool): The format of the time string. If False, use the default format.
        timezone (str or bool): The timezone. If False, use the default timezone.

    Returns:
        str: A string representing the current time in the specified format and timezone.
    """


@inject_implementation()
def get_converted_time_float(fmt=False, timezone=False):
    """
    Specify timezone and format, return the current time as a float.
    Args:
        fmt (str or bool): The format of the time string. If False, use the default format.
        timezone (str or bool): The timezone. If False, use the default timezone.
    Returns:
        float: A float representing the current time in the specified format and timezone.
    """


@inject_implementation()
def get_yes_today(data_str: str, fmt=False, timezone=False):
    """
    Get the previous day's date from the given date string.

    Args:
        data_str (str): The date string.
        fmt (str or bool): The format of the date string. If False, use the default format.
        timezone (str or bool): The timezone. If False, use the default timezone.

    Returns:
        str: A string representing the previous day's date in the specified format and timezone.
    """


@inject_implementation()
def get_yesterday_date(fmt=False, timezone=False, days=1):
    """
    Specify timezone and format, return the previous day's time.

    Args:
        fmt (str or bool): The format of the time string. If False, use the default format.
        timezone (str or bool): The timezone. If False, use the default timezone.
        days (int): The number of days to subtract from the current date. Default is 1.

    Returns:
        str: A string representing the previous day's time in the specified format and timezone.
    """


@inject_implementation()
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


@inject_implementation()
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


@inject_implementation()
def get_date_list(start_day: str, end_day: str):
    """
    Obtain every day within the time range.

    Args:
        start_day (str): The start date in the format '%Y%m%d'.
        end_day (str): The end date in the format '%Y%m%d'.

    Returns:
        list: A list of strings representing each day within the time range in the format '%Y%m%d'.
    """


@inject_implementation()
def get_week_num(date_str: str):
    """
    Obtain a week number from the given date string.
    Args:
        date_str (str): The date string in the format '%Y-%m-%d'.
    Returns:
        int: The week number.
    """


@inject_implementation()
def get_current_week():
    """
    Obtain current week number.
    Returns:
        int: The week number.
    """


@inject_implementation()
def is_timestamp_within_days(timestamp: int, fmt=False, timezone=False):
    """
    Check if a timestamp is within days.
    Args:
        timestamp (int): The timestamp to be checked.
        fmt (str or bool): The format of the time string. If False, use the default format.
        timezone (str or bool): The timezone. If False, use the default timezone.
    Returns:
        bool: True if the timestamp is within days, False otherwise.
    """


@inject_implementation()
def convert_timestamp_to_timezone_obj(timestamp, timezone=False):
    """
    Convert a timestamp to a time string.
    Args:
        timestamp (int): The timestamp to be converted.
        timezone (str or bool): The timezone. If False, use the default timezone.
    Returns:
        datetime.datetime: A datetime object representing the converted time.
    """


@inject_implementation()
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
