# -*- encoding: utf-8 -*-
import os
import sys
import argparse

from astraflux.inject import inject_init
from astraflux.servers.build import Build

from astraflux.settings import *
from astraflux.interface import *


class RunServer:

    def __init__(self, config, cls_path):
        self.config = config
        self.cls_path = cls_path

    def server_start(self):
        build = Build(
            config=self.config,
            cls_path=self.cls_path,
            build_type='service',
            constructor=ServiceConstructor
        )
        constructor = build.build(task_id=None)

        service_data = {
            BUILD.KEY_NAME: constructor.name,
            BUILD.KEY_SERVICE_IPADDR: constructor.service_ipaddr,
            BUILD.KEY_SERVICE_NAME: constructor.service_name,
            BUILD.KEY_SERVICE_VERSION: constructor.service_version,
            BUILD.KEY_SERVICE_PID: os.getpid(),
            BUILD.KEY_SERVICE_FUNCTIONS: constructor.functions
        }

        mongodb_services().update_many(
            query={
                BUILD.KEY_SERVICE_IPADDR: constructor.service_ipaddr,
                BUILD.KEY_SERVICE_NAME: constructor.service_name
            },
            update_data=service_data,
            upsert=True
        )

        constructor.loguru.info('Service started == {}'.format(service_data))

        service_running(
            service_cls=constructor,
            config={RABBITMQ.KEY_RABBITMQ_URI: self.config.get(RABBITMQ.KEY_RABBITMQ_URI)}
        )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="run service script")

    parser.add_argument("--config", type=str, help="service config")
    parser.add_argument("--path", type=str, help="service path")
    args = parser.parse_args()

    inject_init()

    configs = load_config(args.config)

    sys.path.append(configs[KEY_ROOT_PATH])

    RunServer(config=configs, cls_path=args.path).server_start()
