# -*- encoding: utf-8 -*-
import os
import sys
import time
import json
import argparse
import multiprocessing

from astraflux.inject import inject_init
from astraflux.servers.build import Build

from astraflux.settings import *
from astraflux.interface import *


class TaskRun:

    @staticmethod
    def run(cls_path: str, config: dict, body: dict):

        initialization_mongo(config=config)
        initialization_redis(config=config)
        initialization_rabbitmq(config=config)
        initialization_rpc_proxy(config=config)
        initialization_logger(config=config)

        worker_pid = os.getpid()

        build = Build(
            config=config,
            cls_path=cls_path,
            build_type='worker',
            constructor=WorkerConstructor
        )
        constructor: WorkerConstructor = build.build(task_id=body[TASK.KEY_TASK_ID])

        start_ime = get_converted_time()
        mongodb_task().update_many(
            query={TASK.KEY_TASK_ID: body[TASK.KEY_TASK_ID]},
            update_data={
                BUILD.KEY_WORKER_PID: worker_pid,
                BUILD.KEY_WORKER_IPADDR: constructor.worker_ipaddr,
                TASK.KEY_TASK_STATUS: TASK.KEY_TASK_RUN_STATUS,
                TASK.KEY_TASK_START_TIME: start_ime
            }
        )

        mongodb_services().push_one(
            query={
                BUILD.KEY_WORKER_NAME: constructor.worker_name,
                BUILD.KEY_WORKER_IPADDR: constructor.worker_ipaddr
            },
            update_data={
                BUILD.KEY_WORKER_RUN_PROCESS: worker_pid
            }
        )

        try:
            constructor().run(body)
            mongodb_task().update_many(
                query={TASK.KEY_TASK_ID: body[TASK.KEY_TASK_ID]},
                update_data={
                    BUILD.KEY_WORKER_PID: os.getpid(),
                    BUILD.KEY_WORKER_IPADDR: constructor.worker_ipaddr,
                    TASK.KEY_TASK_STATUS: TASK.KEY_TASK_SUCCESS_STATUS,
                    TASK.KEY_TASK_END_TIME: get_converted_time()
                },
                upsert=True
            )
        except Exception as e:
            mongodb_task().update_many(
                query={TASK.KEY_TASK_ID: body[TASK.KEY_TASK_ID]},
                update_data={
                    BUILD.KEY_WORKER_PID: os.getpid(),
                    BUILD.KEY_WORKER_IPADDR: constructor.worker_ipaddr,
                    TASK.KEY_TASK_STATUS: TASK.KEY_TASK_ERROR_STATUS,
                    TASK.KEY_TASK_END_TIME: get_converted_time(),
                    TASK.KEY_TASK_ERROR_MESSAGE: str(e)
                },
                upsert=True
            )

        mongodb_services().pull_one(
            query={
                BUILD.KEY_WORKER_NAME: constructor.worker_name,
                BUILD.KEY_WORKER_IPADDR: constructor.worker_ipaddr
            },
            update_data={
                BUILD.KEY_WORKER_RUN_PROCESS: worker_pid
            }
        )


class RabbitmqCallback:
    """
    RabbitmqCallback is a class that represents a rabbitmq callback.
    It contains attributes such as name, config, loguru, ip_addr,
     cls_path, rpc_proxy, database_tasks, and database_services.
    """

    config = None
    loguru = None
    ip_addr = None
    cls_path = None
    worker_name = None

    def mq_callback(self, ch, method, properties, body):
        """
        Handles the callback for the rabbitmq message.
        Args:
            ch: The channel object.
            method: The method object.
            properties: The properties object.
            body: The body of the message.
        """
        ch.basic_ack(delivery_tag=method.delivery_tag)
        try:
            _body = json.loads(body.decode())
            if TASK.KEY_TASK_ID in _body:

                if BUILD.KEY_SYSTEM_SERVICE_NAME not in self.worker_name:
                    status = redis_get_task_status_by_task_id(task_id=_body.get(TASK.KEY_TASK_ID))
                else:
                    status = TASK.KEY_TASK_RUN_STATUS

                if status != TASK.KEY_TASK_STOP_STATUS:
                    run_worker, max_worker = query_worker_running_number(
                        query={
                            BUILD.KEY_WORKER_NAME: self.worker_name,
                            BUILD.KEY_SERVICE_IPADDR: self.ip_addr
                        }
                    )
                    if run_worker < max_worker:
                        multiprocessing.Process(target=TaskRun.run, args=(self.cls_path, self.config, _body,)).start()
                    else:
                        time.sleep(0.2)
                        ch.basic_publish(body=body, exchange='', routing_key=self.worker_name)
            else:
                self.loguru.error('{} is not find, error data : {}'.format(TASK.KEY_TASK_ID, _body))
        except Exception as e:
            self.loguru.error('mq_callback error: {}'.format(e))


class RunWorker:
    def __init__(self, config, cls_path):
        self.config = config
        self.cls_path = cls_path

    def worker_start(self):
        build = Build(
            config=self.config,
            cls_path=self.cls_path,
            build_type='worker',
            constructor=WorkerConstructor
        )
        constructor: WorkerConstructor = build.build(task_id=None)
        worker_data = {
            BUILD.KEY_NAME: constructor.name,
            BUILD.KEY_WORKER_IPADDR: constructor.worker_ipaddr,
            BUILD.KEY_WORKER_NAME: constructor.worker_name,
            BUILD.KEY_WORKER_VERSION: constructor.worker_version,
            BUILD.KEY_WORKER_PID: os.getpid(),
            BUILD.KEY_WORKER_FUNCTIONS: constructor.functions,
            BUILD.KEY_WORKER_MAX_PROCESS: 10,
            BUILD.KEY_WORKER_RUN_PROCESS: [],
        }

        mongodb_services().update_many(
            query={
                BUILD.KEY_SERVICE_IPADDR: constructor.worker_ipaddr,
                BUILD.KEY_SERVICE_NAME: constructor.worker_name
            },
            update_data=worker_data,
            upsert=True
        )
        constructor.loguru.info('Worker started == {}'.format(worker_data))

        mq_callback = RabbitmqCallback()
        mq_callback.config = self.config
        mq_callback.cls_path = self.cls_path
        mq_callback.loguru = constructor.loguru
        mq_callback.ip_addr = constructor.worker_ipaddr
        mq_callback.worker_name = constructor.worker_name

        while True:
            try:
                rabbitmq_receive_message(queue=constructor.worker_name, callback=mq_callback.mq_callback)
            except Exception as e:
                constructor.loguru.error(' {} work error : {}'.format(constructor.worker_name, e))
            time.sleep(0.5)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="run worker script")

    parser.add_argument("--config", type=str, help="worker config")
    parser.add_argument("--path", type=str, help="worker path")
    args = parser.parse_args()

    inject_init()

    configs = load_config(args.config)

    sys.path.append(configs[KEY_ROOT_PATH])

    RunWorker(config=configs, cls_path=args.path).worker_start()
