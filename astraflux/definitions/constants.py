# -*- coding: utf-8 -*-

from enum import Enum, unique


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

    @unique
    class DEFAULT(Enum):
        HOST = '127.0.0.1'
        PORT = 27017
        DATABASE = 'astraflux'
        USERNAME = 'scheduleAdmin'
        PASSWORD = 'scheduleAdminPassword'


class REDIS:
    @unique
    class CONFIG(Enum):
        KEY = 'redis'
        HOST = 'host'
        PORT = 'port'
        PASSWORD = 'password'
        DB_TASK = 'db_task'
        DB_SERVICE = 'db_service'

    @unique
    class DEFAULT(Enum):
        HOST = '127.0.0.1'
        PORT = 6379
        PASSWORD = 'scheduleAdminPassword'
        DB_TASK = 8
        DB_SERVICE = 9


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


CONFIGS = [
    MONGODB,
    REDIS,
    RABBITMQ,
    LOGGER
]
