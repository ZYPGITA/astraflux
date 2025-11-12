# -*- coding: utf-8 -*-

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
