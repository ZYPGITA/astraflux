# -*- encoding: utf-8 -*-


KEY_PROJECT_VERSION = '1.0'

KEY_PROJECT_NAME = 'astraflux'
KEY_ROOT_PATH = 'current_dir'


class TABLE:
    KEY_TASK_LIST = 'task_list'
    KEY_NODE_LIST = 'node_list'
    KEY_SERVICE_LIST = 'service_list'


class LOG:
    KEY_LOGS_PATH = 'logs'
    KEY_LOGS_FILENAME = 'filename'
    KEY_LOGS_CONFIG_NAME = 'logger'
    KEY_LOGS_CONFIG_LEVEL = 'level'

    DEFAULT_VALUE_LOGS_SUFFIX = "%Y-%m-%d.log"
    DEFAULT_VALUE_LOGS_FMT = '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] %(message)s'


class RABBITMQ:
    KEY_RABBITMQ_URI = 'AMQP_URI'
    KEY_RABBITMQ_CONFIG = 'RABBITMQ_CONFIG'
    KEY_SYSTEM_SERVICE_NAME = 'PSS'
    DEFAULT_VALUE_RABBITMQ_URI = 'amqp://scheduleAdmin:scheduleAdminPassword@127.0.0.1:5672'


class MONGODB:
    KEY_MONGODB_URI = 'MONGODB_URI'
    KEY_MONGO_CONFIG = 'MONGODB_CONFIG'
    DEFAULT_VALUE_MONGODB_URI = 'mongodb://scheduleAdmin:scheduleAdminPassword@127.0.0.1:27017'


class REDIS:
    KEY_REDIS_URI = 'REDIS_URI'
    KEY_REDIS_CONFIG = 'REDIS_CONFIG'
    DEFAULT_VALUE_REDIS_URI = 'redis://:scheduleAdminPassword@127.0.0.1:6379'


class RPC:
    KEY_RPC_CALL_TIMEOUT = 'RPC_CALL_TIMEOUT'
    DEFAULT_VALUE_RPC_CALL_TIMEOUT = 30
    KEY_SYSTEM_SERVICE_NAME = 'proxy'
    KEY_FUNCTION_SELF = 'self'
    KEY_FUNCTION_RPC = 'RpcFunction'
    KEY_FUNCTION_WORKER = 'WorkerFunction'
    KEY_FUNCTION_PARAM_NAME = 'param_name'
    KEY_FUNCTION_PARAM_DEFAULT_VALUE = 'default_value'


class SOCKET:
    SOCKET_BIND_PORT = 80
    SOCKET_BIND_IP = '8.8.8.8'
    SOCKET_SHUTDOWN_SLEEP = 2


class TIME:
    DEFAULT_VALUE_TIMEZONE = 'Asia/Shanghai'
    DEFAULT_VALUE_TIME_FMT = '%Y%m%d%H%M%S'


class BUILD:
    KEY_WORKER_PID = 'worker_pid'
    KEY_WORKER_NAME = 'worker_name'
    KEY_WORKER_IPADDR = 'worker_ipaddr'
    KEY_WORKER_VERSION = 'worker_version'
    KEY_WORKER_FUNCTIONS = 'worker_functions'
    KEY_WORKER_MAX_PROCESS = 'worker_max_process'
    KEY_WORKER_RUN_PROCESS = 'worker_run_process'

    KEY_NAME = 'name'
    KEY_SERVICE_PID = 'service_pid'
    KEY_SERVICE_NAME = 'service_name'
    KEY_SERVICE_IPADDR = 'service_ipaddr'
    KEY_SERVICE_VERSION = 'service_version'
    KEY_SERVICE_FUNCTIONS = 'service_functions'

    KEY_SYSTEM_SERVICE_NAME = 'proxy_system_server'


class TASK:
    DEFAULT_VALUE_TASK_WEIGHT = 1

    KEY_TASK_BODY = 'body'
    KEY_TASK_ID = 'task_id'
    KEY_TASK_WEIGHT = 'weight'
    KEY_TASK_STATUS = 'status'
    KEY_TASK_SOURCE_ID = 'source_id'
    KEY_TASK_QUEUE_NAME = 'queue_name'
    KEY_TASK_IS_SUB_TASK = 'is_subtask'
    KEY_TASK_IS_SUB_TASK_ALL_FINISH = 'is_subtask_all_finish'

    KEY_TASK_WAIT_STATUS = 'wait'
    KEY_TASK_SEND_STATUS = 'send'
    KEY_TASK_STOP_STATUS = 'stop'
    KEY_TASK_ERROR_STATUS = 'error'
    KEY_TASK_RUN_STATUS = 'running'
    KEY_TASK_SUCCESS_STATUS = 'success'
    KEY_TASK_ERROR_MESSAGE = 'error_message'

    KEY_TASK_END_TIME = 'end_time'
    KEY_TASK_START_TIME = 'start_time'
    KEY_TASK_CREATE_TIME = 'create_time'


class SCHEDULE:
    DEFAULT_VALUE_SCHEDULE_TIME = 10
    KEY_DEFAULT_SCHEDULE_TIME = 'DEFAULT_SCHEDULE_TIME'
    KEY_NODE_IPADDR = 'ipaddr'
