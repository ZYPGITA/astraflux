# -*- encoding: utf-8 -*-

import pytz
import datetime
from calendar import monthrange

__all__ = ['CronParser']


class CronParser:

    def __init__(self, cron_str: str, timezone: str = pytz.utc):
        """
        Initializes the CronParser with a cron expression and an optional timezone.
        Args:
            cron_str (str): The cron expression string.
            timezone (Union[str, datetime.tzinfo], optional): The timezone to use for the cron expression.
                Defaults to pytz.utc.
        """

        self.cron_parts = cron_str.split()
        if len(self.cron_parts) != 6:
            raise ValueError("Invalid cron expression (Need 6 parts: second minute hour day month weekday)")

        self.timezone = timezone
        if isinstance(self.timezone, str):
            self.timezone = pytz.timezone(self.timezone)

        self.second = self._parse_part(self.cron_parts[0], 0, 59)
        self.minute = self._parse_part(self.cron_parts[1], 0, 59)
        self.hour = self._parse_part(self.cron_parts[2], 0, 23)
        self.day = self._parse_part(self.cron_parts[3], 1, 31)
        self.month = self._parse_part(self.cron_parts[4], 1, 12)
        self.weekday = self._parse_part(self.cron_parts[5], 0, 6)

    @staticmethod
    def _parse_part(part: str, min_val: int, max_val: int) -> set:
        """
        Parses a part of the cron expression and returns a set of valid values.
        Args:
            part (str): The part of the cron expression to parse.
            min_val (int): The minimum valid value for the part.
            max_val (int): The maximum valid value for the part.
        Returns:
            set: A set of valid values for the part.
        """
        if part == "*":
            return set(range(min_val, max_val + 1))
        values = set()
        for item in part.split(","):
            if "/" in item:
                step = int(item.split("/")[1])
                values.update(range(min_val, max_val + 1, step))
            elif "-" in item:
                start, end = map(int, item.split("-"))
                values.update(range(start, end + 1))
            else:
                values.add(int(item))
        return values

    def get_next_run(self, current_time: datetime.datetime):
        """
        Calculates the next run time based on the cron expression and the current time.
        Args:
            current_time (datetime): The current time.
        Returns:
            datetime: The next run time.
        """

        localized_time = current_time.astimezone(self.timezone)
        next_time = localized_time + datetime.timedelta(seconds=1)

        while True:

            if next_time.month not in self.month:
                next_time = next_time.replace(
                    day=1,
                    month=(next_time.month + 1) if next_time.month < 12 else 1,
                    year=(next_time.year + 1) if next_time.month == 12 else next_time.year,
                    hour=0, minute=0, second=0
                )
                continue

            day_valid = next_time.day in self.day
            weekday_valid = next_time.weekday() in self.weekday
            if not (day_valid or weekday_valid):
                next_time += datetime.timedelta(days=1)
                next_time = next_time.replace(hour=0, minute=0, second=0)
                continue

            if (
                    next_time.second in self.second
                    and next_time.minute in self.minute
                    and next_time.hour in self.hour
            ):
                return next_time.astimezone(pytz.utc)

            next_time += datetime.timedelta(seconds=1)

            if next_time.day > monthrange(next_time.year, next_time.month)[1]:
                next_time = next_time.replace(
                    day=1,
                    month=(next_time.month + 1) if next_time.month < 12 else 1,
                    year=(next_time.year + 1) if next_time.month == 12 else next_time.year,
                    hour=0, minute=0, second=0
                )
