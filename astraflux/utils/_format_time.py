# -*- encoding: utf-8 -*-
import pytz
import datetime

from astraflux.settings.keys import *

_fmt = TIME.DEFAULT_VALUE_TIME_FMT
_timezone = TIME.DEFAULT_VALUE_TIMEZONE


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
        fmt = _fmt

    if timezone is False:
        timezone = _timezone

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


def get_converted_time_float(fmt=False, timezone=False):
    """
    Specify timezone and format, return the current time as a float.
    Args:
        fmt (str or bool): The format of the time string. If False, use the default format.
        timezone (str or bool): The timezone. If False, use the default timezone.
    Returns:
        float: A float representing the current time in the specified format and timezone.
    """
    return float(get_converted_time(fmt, timezone))


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
    fmt, timezone = _get_default_params(fmt, timezone)

    day = datetime.datetime.strptime(data_str, fmt)
    delta = datetime.timedelta(days=-1)

    target_timezone = pytz.timezone(timezone)
    converted_time = day.astimezone(target_timezone)

    return (converted_time + delta).strftime(fmt)


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
    fmt, timezone = _get_default_params(fmt, timezone)
    current_time = datetime.datetime.now()
    target_timezone = pytz.timezone(timezone)
    converted_time = current_time.astimezone(target_timezone)

    return (converted_time - datetime.timedelta(days=days)).strftime(fmt)


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


def get_date_list(start_day: str, end_day: str):
    """
    Obtain every day within the time range.

    Args:
        start_day (str): The start date in the format '%Y%m%d'.
        end_day (str): The end date in the format '%Y%m%d'.

    Returns:
        list: A list of strings representing each day within the time range in the format '%Y%m%d'.
    """
    start_date = datetime.datetime.strptime(start_day, '%Y%m%d')
    end_date = datetime.datetime.strptime(end_day, '%Y%m%d')

    date_list = []
    current_date = start_date

    while current_date <= end_date:
        date_list.append(current_date.strftime('%Y%m%d'))
        current_date += datetime.timedelta(days=1)

    return date_list


def get_week_num(date_str: str):
    """
    Obtain a week number from the given date string.
    Args:
        date_str (str): The date string in the format '%Y-%m-%d'.
    Returns:
        int: The week number.
    """
    now_time = datetime.datetime.strptime(date_str + " 00:00:00", "%Y-%m-%d %H:%M:%S")
    one_time = now_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    week_num = int(now_time.strftime('%W')) - int(one_time.strftime('%W')) + 1
    return week_num


def get_current_week():
    """
    Obtain current week number.
    Returns:
        int: The week number.
    """
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    return [datetime.datetime.strftime((monday + datetime.timedelta(days=i)), "%Y%m%d") for i in range(7)]


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
    fmt, timezone = _get_default_params(fmt, timezone)
    datetime_utc = datetime.datetime.utcfromtimestamp(timestamp)
    timezone_obj = pytz.timezone(timezone)
    datetime_timezone = datetime_utc.replace(tzinfo=pytz.utc).astimezone(timezone_obj)
    current_time = datetime.datetime.now()
    target_timezone = pytz.timezone(timezone)
    converted_time = current_time.astimezone(target_timezone)
    return (converted_time - datetime_timezone).days


def convert_timestamp_to_timezone_obj(timestamp, timezone=False):
    """
    Convert a timestamp to a time string.
    Args:
        timestamp (int): The timestamp to be converted.
        timezone (str or bool): The timezone. If False, use the default timezone.
    Returns:
        datetime.datetime: A datetime object representing the converted time.
    """
    fmt, timezone = _get_default_params(fmt=False, timezone=timezone)
    datetime_utc = datetime.datetime.utcfromtimestamp(timestamp)
    timezone_obj = pytz.timezone(timezone)
    datetime_timezone = datetime_utc.replace(tzinfo=pytz.utc).astimezone(timezone_obj)
    return datetime_timezone


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


def register():
    from astraflux.interface import format_time
    format_time.get_date_time_obj = get_date_time_obj
    format_time.format_converted_time = format_converted_time
    format_time.get_converted_time = get_converted_time
    format_time.get_yes_today = get_yes_today
    format_time.get_yesterday_date = get_yesterday_date
    format_time.convert_timestamp_to_timezone = convert_timestamp_to_timezone
    format_time.get_converted_timestamp = get_converted_timestamp
    format_time.get_date_list = get_date_list
    format_time.get_week_num = get_week_num
    format_time.get_current_week = get_current_week
    format_time.is_timestamp_within_days = is_timestamp_within_days
    format_time.convert_timestamp_to_timezone_obj = convert_timestamp_to_timezone_obj
    format_time.convert_timestamp_to_timezone_str = convert_timestamp_to_timezone_str
    format_time.get_converted_time_float = get_converted_time_float

    import sys
    sys.modules['astraflux.interface.format_time'] = format_time
