# -*- encoding: utf-8 -*-
from enum import Enum

PROJECT_VERSION = '2.0'
PROJECT_NAME = 'astraflux'

REPLACE_SYS_MODULE = False


class FrozenClass:
    __slots__ = ()

    def __setattr__(self, name, value):
        raise AttributeError(f"Cannot modify constant {name}")


class DEFINITIONS:
    SYSTEM_SERVICE_NAME = 'proxy_system_server'

    class STATUS(Enum):
        PENDING = "pending"
        RUNNING = "running"
        SUCCESS = "success"
        FAILED = "failed"
        RETRYING = "retrying"
        STOPPED = "stopped"
        WAITING = "waiting"

    class RPC(FrozenClass):
        CALL_TIMEOUT = 'RPC_CALL_TIMEOUT'
        PROXY = 'proxy'
        FUNCTION_SELF = 'self'
        FUNCTION_RPC = 'RpcFunction'
        FUNCTION_WORKER = 'WorkerFunction'
        FUNCTION_PARAM_NAME = 'param_name'
        FUNCTION_PARAM_DEFAULT_VALUE = 'default_value'

    class BUILD(FrozenClass):
        NAME = 'name'

        WORKER_PID = 'worker_pid'
        WORKER_NAME = 'worker_name'
        WORKER_IPADDR = 'worker_ipaddr'
        WORKER_VERSION = 'worker_version'
        WORKER_FUNCTIONS = 'worker_functions'
        WORKER_MAX_PROCESS = 'worker_max_process'
        WORKER_RUN_PROCESS = 'worker_run_process'

        SERVICE_PID = 'service_pid'
        SERVICE_NAME = 'service_name'
        SERVICE_IPADDR = 'service_ipaddr'
        SERVICE_VERSION = 'service_version'
        SERVICE_FUNCTIONS = 'service_functions'

    class TASK(FrozenClass):
        BODY = 'body'
        ID = 'task_id'
        WEIGHT = 'weight'
        STATUS = 'status'
        SOURCE_ID = 'source_id'
        QUEUE_NAME = 'queue_name'
        IS_SUB_TASK = 'is_subtask'
        IS_SUB_TASK_ALL_FINISH = 'is_subtask_all_finish'

        END_TIME = 'end_time'
        START_TIME = 'start_time'
        CREATE_TIME = 'create_time'

        ERROR_MESSAGE = 'error_message'

    class SCHEDULE(FrozenClass):
        DEFAULT_SCHEDULE_TIME = 'DEFAULT_SCHEDULE_TIME'
        NODE_IPADDR = 'ipaddr'

    class TABLE(FrozenClass):
        NODE_LIST = 'node_list'
        TASK_LIST = 'task_list'
        SERVICE_LIST = 'service_list'


class DefaultValues:
    class LOG(FrozenClass):
        SUFFIX = "%Y-%m-%d.log"
        FMT = '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] %(message)s'

    class RABBITMQ(FrozenClass):
        RABBITMQ_URI = 'amqp://scheduleAdmin:scheduleAdminPassword@127.0.0.1:5672'

    class MONGODB(FrozenClass):
        MONGODB_URI = 'mongodb://scheduleAdmin:scheduleAdminPassword@127.0.0.1:27017'

    class REDIS(FrozenClass):
        REDIS_URI = 'redis://:scheduleAdminPassword@127.0.0.1:6379'
        TASK_DB_INDEX = 0
        SERVICE_DB_INDEX = 1

    class RPC(FrozenClass):
        RPC_CALL_TIMEOUT = 30

    class SOCKET(FrozenClass):
        BIND_PORT = 80
        BIND_IP = '8.8.8.8'
        SHUTDOWN_SLEEP = 2

    class TIME(FrozenClass):
        TIMEZONE = 'Asia/Shanghai'
        TIME_FMT = '%Y%m%d%H%M%S'

    class TASK(FrozenClass):
        WEIGHT = 1

    class SCHEDULE(FrozenClass):
        SCHEDULE_TIME = 10


class ConfigKeys:
    USERNAME = 'username'
    PASSWORD = 'password'
    HOST = 'host'
    PORT = 'port'

    FILENAME = 'filename'
    CURRENT_DIR = 'current_dir'

    class LOG(FrozenClass):
        KEY = 'logger'
        LOG_PATH = 'path'
        LOG_LEVEL = 'level'

    class RABBITMQ(FrozenClass):
        KEY = 'rabbitmq'
        RABBITMQ_URI = 'uri'

    class MONGODB(FrozenClass):
        KEY = 'mongodb'
        MONGODB_URI = 'uri'

    class REDIS(FrozenClass):
        KEY = 'redis'
        REDIS_URI = 'uri'
