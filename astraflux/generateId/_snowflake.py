# -*- encoding: utf-8 -*-

import time
from astraflux.interface import *


class SnowflakeID:
    """
    A singleton class that generates unique IDs based on the Snowflake algorithm.
    This algorithm ensures that the generated IDs are unique across different machines and time.
    """

    _instance = None
    __initialized = False

    def __new__(cls, *args, **kwargs):
        """
        Overrides the __new__ method to implement the singleton pattern.
        Ensures that only one instance of the Snowflake class is created.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Snowflake: The singleton instance of the Snowflake class.
        """

        if not cls._instance:
            cls._instance = super(SnowflakeID, cls).__new__(cls)
            cls._instance.__initialized = False
        return cls._instance

    def __init__(self, datacenter_id: int = None, machine_id: int = None, sequence: int = 0):
        """
        Initializes the Snowflake ID generator.

        Args:
            datacenter_id (int, optional): The ID of the data center. Defaults to None.
            machine_id (int, optional): The ID of the machine. Defaults to None.
            sequence (int, optional): The initial sequence number. Defaults to 0.
        """
        if self.__initialized:
            return

        self.__initialized = True
        self.ipaddress = get_ipaddr()

        self.start_timestamp = 1288834974657

        self.datacenter_id_bits = 5
        self.machine_id_bits = 5
        self.sequence_bits = 12

        self.max_datacenter_id = (1 << self.datacenter_id_bits) - 1
        self.max_machine_id = (1 << self.machine_id_bits) - 1
        self.max_sequence = (1 << self.sequence_bits) - 1

        self.machine_id_shift = self.sequence_bits
        self.datacenter_id_shift = self.sequence_bits + self.machine_id_bits
        self.timestamp_left_shift = self.sequence_bits + self.machine_id_bits + self.datacenter_id_bits

        if datacenter_id is not None:
            self.datacenter_id = datacenter_id
        else:
            self.datacenter_id = int(self.ipaddress.split('.')[-2])

        if machine_id is not None:
            self.machine_id = machine_id
        else:
            self.machine_id: int = int(self.ipaddress.split('.')[-1])

        self.sequence = sequence
        self.last_timestamp = -1

    @staticmethod
    def _current_timestamp():
        """
        Returns the current timestamp in milliseconds.

        Returns:
            int: The current timestamp in milliseconds.
        """
        return int(time.time() * 1000)

    def _till_next_millis(self, last_timestamp):
        """
        Waits until the next millisecond to ensure the timestamp is greater than the last one.

        Args:
            last_timestamp (int): The last timestamp used to generate an ID.

        Returns:
            int: The new timestamp.
        """
        timestamp = self._current_timestamp()
        while timestamp <= last_timestamp:
            timestamp = self._current_timestamp()
        return timestamp

    @property
    def generate_id(self) -> str:
        """
        Generates a Snowflake ID using the Snowflake algorithm.

        Returns:
            str: A Snowflake ID.
        """
        timestamp = self._current_timestamp()

        if timestamp < self.last_timestamp:
            raise Exception("Clock moved backwards. Refusing to generate id")

        if self.last_timestamp == timestamp:
            self.sequence = (self.sequence + 1) & self.max_sequence
            if self.sequence == 0:
                timestamp = self._till_next_millis(self.last_timestamp)
        else:
            self.sequence = 0

        self.last_timestamp = timestamp

        _id = ((timestamp - self.start_timestamp) << self.timestamp_left_shift) | \
              (self.datacenter_id << self.datacenter_id_shift) | \
              (self.machine_id << self.machine_id_shift) | self.sequence

        return str(_id)


def snowflake_id() -> str:
    """
    Returns a Snowflake ID generator function.
    Returns:
        function: A function that generates Snowflake IDs.
    """
    return SnowflakeID().generate_id


def register():
    from astraflux.interface import snowflake
    snowflake.snowflake_id = snowflake_id

    import sys
    sys.modules['astraflux.interface.snowflake'] = snowflake
