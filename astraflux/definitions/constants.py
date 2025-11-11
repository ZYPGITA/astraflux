# -*- encoding: utf-8 -*-

PROJECT_VERSION = '2.0'
PROJECT_NAME = 'astraflux'

REPLACE_SYS_MODULE = False


class FrozenClass:
    __slots__ = ()

    def __setattr__(self, name, value):
        raise AttributeError(f"Cannot modify constant {name}")


class DEFINITIONS:
    SYSTEM_SERVICE_NAME = 'proxy_system_server'

    class RPC(FrozenClass):
        CALL_TIMEOUT = 'RPC_CALL_TIMEOUT'
        PROXY = 'proxy'
        FUNCTION_SELF = 'self'
        FUNCTION_RPC = 'RpcFunction'
        FUNCTION_WORKER = 'WorkerFunction'
        FUNCTION_PARAM_NAME = 'param_name'
        FUNCTION_PARAM_DEFAULT_VALUE = 'default_value'

    class BUILD(FrozenClass):
        WORKER_PID = 'worker_pid'
        WORKER_NAME = 'worker_name'
        WORKER_IPADDR = 'worker_ipaddr'
        WORKER_VERSION = 'worker_version'
        WORKER_FUNCTIONS = 'worker_functions'
        WORKER_MAX_PROCESS = 'worker_max_process'
        WORKER_RUN_PROCESS = 'worker_run_process'

        NAME = 'name'
        SERVICE_PID = 'service_pid'
        SERVICE_NAME = 'service_name'
        SERVICE_IPADDR = 'service_ipaddr'
        SERVICE_VERSION = 'service_version'
        SERVICE_FUNCTIONS = 'service_functions'

    class TASK(FrozenClass):
        TASK_BODY = 'body'
        TASK_ID = 'task_id'
        TASK_WEIGHT = 'weight'
        TASK_STATUS = 'status'
        TASK_SOURCE_ID = 'source_id'
        TASK_QUEUE_NAME = 'queue_name'
        TASK_IS_SUB_TASK = 'is_subtask'
        TASK_IS_SUB_TASK_ALL_FINISH = 'is_subtask_all_finish'

        TASK_WAIT_STATUS = 'wait'
        TASK_SEND_STATUS = 'send'
        TASK_STOP_STATUS = 'stop'
        TASK_ERROR_STATUS = 'error'
        TASK_RUN_STATUS = 'running'
        TASK_SUCCESS_STATUS = 'success'
        TASK_ERROR_MESSAGE = 'error_message'

        TASK_END_TIME = 'end_time'
        TASK_START_TIME = 'start_time'
        TASK_CREATE_TIME = 'create_time'

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
        TASK_WEIGHT = 1

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
