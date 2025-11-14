# -*- encoding: utf-8 -*-

import pytz
import datetime
from typing import Union, Optional, Set


class AdvancedCronScheduler:
    """
    Advanced Cron Scheduler with second-level precision and timezone support
    Supports format: second minute hour day month weekday
    """

    def __init__(self, cron_expression: str, timezone: Union[str, datetime.tzinfo] = pytz.UTC):
        """
        Initialize Cron Scheduler

        Args:
            cron_expression: Cron expression (6 parts: second minute hour day month weekday)
            timezone: Timezone, supports string or tzinfo object

        Raises:
            ValueError: When cron expression is invalid
        """
        self.cron_parts = cron_expression.strip().split()
        if len(self.cron_parts) != 6:
            raise ValueError("Invalid cron expression (requires 6 parts: second minute hour day month weekday)")

        self.timezone = self._parse_timezone(timezone)

        self.second_field = self._parse_field(self.cron_parts[0], 0, 59, "second")
        self.minute_field = self._parse_field(self.cron_parts[1], 0, 59, "minute")
        self.hour_field = self._parse_field(self.cron_parts[2], 0, 23, "hour")
        self.day_field = self._parse_field(self.cron_parts[3], 1, 31, "day")
        self.month_field = self._parse_field(self.cron_parts[4], 1, 12, "month")
        self.weekday_field = self._parse_field(self.cron_parts[5], 0, 6, "weekday")

    @staticmethod
    def _parse_timezone(timezone: Union[str, datetime.tzinfo]) -> datetime.tzinfo:
        """Parse timezone configuration"""
        if isinstance(timezone, str):
            return pytz.timezone(timezone)
        elif isinstance(timezone, datetime.tzinfo):
            return timezone
        else:
            raise ValueError(f"Unsupported timezone type: {type(timezone)}")

    @staticmethod
    def _parse_field(field_str: str, min_val: int, max_val: int, field_name: str) -> Set[int]:
        """
        Parse cron field and return set of valid values

        Args:
            field_str: Field string to parse
            min_val: Minimum allowed value for this field
            max_val: Maximum allowed value for this field
            field_name: Field name (for error messages)

        Returns:
            Set of valid values for this field

        Raises:
            ValueError: When field format is invalid
        """
        if field_str == "*":
            return set(range(min_val, max_val + 1))

        values = set()
        components = field_str.split(",")

        for component in components:
            component = component.strip()
            if not component:
                continue

            if "/" in component:
                range_part, step_part = component.split("/", 1)
                step = int(step_part)
                if step <= 0:
                    raise ValueError(f"{field_name} field step must be positive: {step}")

                if range_part == "*":
                    start, end = min_val, max_val
                elif "-" in range_part:
                    start, end = map(int, range_part.split("-"))
                else:
                    start = end = int(range_part)

                if not (min_val <= start <= end <= max_val):
                    raise ValueError(f"{field_name} field range invalid: {start}-{end}")

                values.update(range(start, end + 1, step))

            elif "-" in component:
                start, end = map(int, component.split("-"))
                if not (min_val <= start <= end <= max_val):
                    raise ValueError(f"{field_name} field range invalid: {start}-{end}")
                values.update(range(start, end + 1))

            else:
                value = int(component)
                if not (min_val <= value <= max_val):
                    raise ValueError(f"{field_name} field value out of range: {value}")
                values.add(value)

        return values

    def get_next_execution_time(self, from_time: Optional[datetime.datetime] = None) -> datetime.datetime | None:
        """
        Calculate the next execution time based on cron expression

        Args:
            from_time: Starting time for calculation, defaults to current time if None

        Returns:
            Next execution time (in UTC timezone)
        """
        if from_time is None:
            from_time = datetime.datetime.now(pytz.UTC)

        local_time = from_time.astimezone(self.timezone)

        candidate = local_time + datetime.timedelta(seconds=1)
        candidate = candidate.replace(microsecond=0)

        while True:
            if candidate.month not in self.month_field:
                candidate = self._next_month(candidate)
                continue

            day_valid = candidate.day in self.day_field
            weekday_valid = candidate.weekday() in self.weekday_field

            if not (day_valid or weekday_valid):
                candidate = self._next_day(candidate)
                continue

            if candidate.hour not in self.hour_field:
                candidate = self._next_hour(candidate)
                continue

            if candidate.minute not in self.minute_field:
                candidate = self._next_minute(candidate)
                continue

            if candidate.second not in self.second_field:
                candidate = self._next_second(candidate)
                continue

            return candidate.astimezone(pytz.UTC)

        return None

    @staticmethod
    def _next_month(dt: datetime.datetime) -> datetime.datetime:
        """Advance to first day of next month"""
        next_month = dt.month + 1
        next_year = dt.year
        if next_month > 12:
            next_month = 1
            next_year += 1
        return dt.replace(
            year=next_year, month=next_month, day=1,
            hour=0, minute=0, second=0
        )

    @staticmethod
    def _next_day(dt: datetime.datetime) -> datetime.datetime:
        """Advance to beginning of next day"""
        next_day = dt + datetime.timedelta(days=1)
        return next_day.replace(hour=0, minute=0, second=0)

    @staticmethod
    def _next_hour(dt: datetime.datetime) -> datetime.datetime:
        """Advance to beginning of next hour"""
        next_hour = dt + datetime.timedelta(hours=1)
        return next_hour.replace(minute=0, second=0)

    @staticmethod
    def _next_minute(dt: datetime.datetime) -> datetime.datetime:
        """Advance to beginning of next minute"""
        next_minute = dt + datetime.timedelta(minutes=1)
        return next_minute.replace(second=0)

    @staticmethod
    def _next_second(dt: datetime.datetime) -> datetime.datetime:
        """Advance to next second"""
        return dt + datetime.timedelta(seconds=1)

    def get_next_n_executions(self, n: int, from_time: Optional[datetime.datetime] = None) -> list[datetime.datetime]:
        """
        Get the next n execution times

        Args:
            n: Number of execution times to retrieve
            from_time: Starting time for calculation

        Returns:
            List of execution times in chronological order
        """
        if n <= 0:
            return []

        executions = []
        current_time = from_time

        for _ in range(n):
            next_time = self.get_next_execution_time(current_time)
            executions.append(next_time)
            current_time = next_time

        return executions

    def validate_schedule(self) -> bool:
        """
        Validate if the cron expression is valid and can produce execution times

        Returns:
            Boolean indicating if expression is valid
        """
        try:
            test_time = datetime.datetime(2020, 1, 1, tzinfo=pytz.UTC)
            self.get_next_execution_time(test_time)
            return True
        except Exception as e:
            print(e)
            return False

    @property
    def cron_expression(self) -> str:
        """Return the cron expression as string"""
        return " ".join(self.cron_parts)

    @property
    def timezone_name(self) -> str:
        """Return timezone name"""
        return str(self.timezone)
