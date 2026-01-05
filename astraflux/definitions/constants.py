# -*- coding: utf-8 -*-

from enum import Enum, unique


@unique
class STATUS(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    STOPPED = "stopped"
    WAITING = "waiting"


@unique
class PROJECT(Enum):
    NAME = 'astraflux'
    CURRENT_DIR = 'current_dir'


@unique
class Scope(Enum):
    SINGLETON = "singleton"
    GLOBAL = "global"
    THREAD = "thread"


class MONGODB:
    @unique
    class CONFIG(Enum):
        KEY = 'mongodb'
        HOST = 'host'
        PORT = 'port'
        DATABASE = 'database'
        USERNAME = 'username'
        PASSWORD = 'password'
        MAX_CONNECTIONS = 'max_connections'

    @unique
    class DEFAULT(Enum):
        HOST = '127.0.0.1'
        PORT = 27017
        DATABASE = 'astraflux'
        USERNAME = 'scheduleAdmin'
        PASSWORD = 'scheduleAdminPassword'
        MAX_CONNECTIONS = 20


class REDIS:
    @unique
    class CONFIG(Enum):
        KEY = 'redis'
        HOST = 'host'
        PORT = 'port'
        PASSWORD = 'password'
        DB_INDEX = 'db_index'
        MAX_CONNECTIONS = 'max_connections'

    @unique
    class DEFAULT(Enum):
        HOST = '127.0.0.1'
        PORT = 6379
        PASSWORD = 'scheduleAdminPassword'
        DB_INDEX = 8
        MAX_CONNECTIONS = 20


class RABBITMQ:
    @unique
    class CONFIG(Enum):
        KEY = 'rabbitmq'
        HOST = 'host'
        PORT = 'port'
        USERNAME = 'username'
        PASSWORD = 'password'

    @unique
    class DEFAULT(Enum):
        HOST = '127.0.0.1'
        PORT = 5672
        USERNAME = 'scheduleAdmin'
        PASSWORD = 'scheduleAdminPassword'


class LOGGER:
    @unique
    class CONFIG(Enum):
        KEY = 'logger'
        PATH = 'path'
        LEVEL = 'level'

    @unique
    class DEFAULT(Enum):
        PATH = 'logs'
        LEVEL = 'INFO'
        SUFFIX = "%Y-%m-%d.log"
        FMT = '%(asctime)s - %(levelname)s - [%(threadName)s] - [%(filename)s:%(lineno)d] %(message)s'


class SOCKET:
    @unique
    class DEFAULT(Enum):
        BIND_IP = '127.0.0.1'
        BIND_PORT = 80


class TIME:
    @unique
    class DEFAULT(Enum):
        TIME_FMT = '%Y-%m-%d %H:%M:%S'
        TIMEZONE = 'Asia/Shanghai'


class RPC:
    @unique
    class DEFAULT(Enum):
        RPC_CALL_TIMEOUT = 30


class TASK:
    @unique
    class CONFIG(Enum):
        ID = 'task_id'
        STATUS = 'status'

        BODY = 'body'
        WEIGHT = 'weight'
        QUEUE_NAME = 'queue_name'

        END_TIME = 'end_time'
        START_TIME = 'start_time'
        CREATE_TIME = 'create_time'
        ERROR_MESSAGE = 'error_message'

        SOURCE_ID = 'source_id'
        RESOURCES = 'resources'
        DEPENDS_ON = 'depends_on'

    class DEFAULT(Enum):
        WEIGHT = 1
        STATUS = STATUS.WAITING.value
        SOURCE_ID = None
        RESOURCES = None
        DEPENDS_ON = None


CONFIGS = [
    MONGODB,
    REDIS,
    RABBITMQ,
    LOGGER
]
