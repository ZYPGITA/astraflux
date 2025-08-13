# -*- encoding: utf-8 -*-

import json
import psutil
import platform

from astraflux.settings import *
from astraflux.interface import *


class PlatformInfo:
    """
    A class that retrieves and stores information about the operating system platform.
    """

    def __init__(self):
        """
        Initialize the PlatformInfo object.
        Retrieves system, release, version, machine, and processor information.
        """
        self.name = platform.system()
        self.release = platform.release()
        self.version = platform.version()
        self.machine = platform.machine()
        self.processor = platform.processor()

    def __str__(self):
        """
        Return a JSON string representation of the PlatformInfo object.
        """
        return json.dumps(self.__dict__)

    def __repr__(self):
        """
        Return a string representation of the PlatformInfo object.
        """
        return self.__str__()


class MemoryInfo:
    """
    A class that retrieves and stores information about the system's memory usage.
    """

    def __init__(self):
        """
        Initialize the MemoryInfo object.
        Retrieves total, available, used, and percentage of memory.
        """
        memory_info = psutil.virtual_memory()
        self.memory_total = round(memory_info.total / (1024 ** 3), 2)
        self.memory_available = round(memory_info.available / (1024 ** 3), 2)
        self.memory_used = round(memory_info.used / (1024 ** 3), 2)
        self.memory_percent = memory_info.percent

    def __str__(self):
        """
        Return a JSON string representation of the MemoryInfo object.
        """
        return json.dumps(self.__dict__)

    def __repr__(self):
        """
        Return a string representation of the MemoryInfo object.
        """
        return self.__str__()


class DiskInfo:
    """
    A class that retrieves and stores information about the system's disk usage.
    """

    def __init__(self):
        """
        Initialize the DiskInfo object.
        Retrieves total, used, free, and percentage of disk space.
        """
        disk_info = psutil.disk_usage('/')
        self.disk_total = round(disk_info.total / (1024 ** 3), 2)
        self.disk_used = round(disk_info.used / (1024 ** 3), 2)
        self.disk_free = round(disk_info.free / (1024 ** 3), 2)
        self.disk_percent = disk_info.percent

    def __str__(self):
        """
        Return a JSON string representation of the DiskInfo object.
        """
        return json.dumps(self.__dict__)

    def __repr__(self):
        """
        Return a string representation of the DiskInfo object.
        """
        return self.__str__()


class CPUInfo:
    """
    A class that retrieves and stores information about the system's CPU usage.
    """

    def __init__(self):
        """
        Initialize the CPUInfo object.
        Retrieves CPU count, percentage, maximum, minimum, and current frequency.
        """
        self.cpu_count = psutil.cpu_count()
        self.cpu_percent = psutil.cpu_percent(interval=1)
        self.cpu_freq_max = psutil.cpu_freq().max
        self.cpu_freq_min = psutil.cpu_freq().min
        self.cpu_freq_current = psutil.cpu_freq().current

    def __str__(self):
        """
        Return a JSON string representation of the CPUInfo object.
        """
        return json.dumps(self.__dict__)

    def __repr__(self):
        """
        Return a string representation of the CPUInfo object.
        """
        return self.__str__()


class NodeInfo:
    """
    A class that aggregates system information into a single node information object.
    """

    def __init__(self):
        """
        Initialize the _NodeInfo object.
        Retrieves node name, IP address, platform, memory, disk, CPU information, and update time.
        """
        self.name = platform.node()
        self.ipaddr = get_ipaddr()
        self.platform = PlatformInfo()
        self.memory = MemoryInfo()
        self.disk = DiskInfo()
        self.cpu = CPUInfo()

        self.update_time = get_converted_time('%Y-%m-%d %H:%M:%S')

        self.node = {
            'name': self.name,
            'ipaddr': self.ipaddr,
            'platform': self.platform.__dict__,
            'memory': self.memory.__dict__,
            'disk': self.disk.__dict__,
            'cpu': self.cpu.__dict__,
            'update_time': self.update_time
        }


class SystemMonitoring:
    """
    A class responsible for performing heartbeat detection.
    It continuously monitors the node's information and updates the database accordingly.
    """

    def __init__(self, config: dict):
        """
        Initialize the HeartbeatDetection instance.
        Args:
            config (dict): Configuration dictionary containing necessary settings.
        """
        initialization_logger(config=config)
        initialization_mongo(config=config)
        self.loguru = loguru(filename=KEY_PROJECT_NAME, task_id='system_monitoring')

    def run(self):
        """
            Start the heartbeat detection process.
            This method runs in an infinite loop, periodically checking the node's information
            and updating the database. If an exception occurs, it logs the error and continues.
        """
        node_info = NodeInfo()
        self.loguru.info(f"{node_info.node}")
        mongodb_node().update_many(
            query={SCHEDULE.KEY_NODE_IPADDR: node_info.ipaddr},
            update_data=node_info.node,
            upsert=True
        )
