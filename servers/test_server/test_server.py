# -*- coding: utf-8 -*-
import time

from astraflux import *


class RpcFunction(ServiceConstructor):
    service_name = 'test_server'

    @rpc_decorator
    def get_service_name(self):
        return {"service_version": self.ipaddr}

    @rpc_decorator
    def test_func(self, **args):
        return args


class WorkerFunction(WorkerConstructor):
    worker_name = 'test_server'

    def run(self, data):
        self.logger.info(data)
        time.sleep(5)
        self.logger.info(f"worker done {data['task_id']}")
