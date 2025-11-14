# -*- encoding: utf-8 -*-

import os
import time

from astraflux import *

from servers.test_server import test_server, sub_test_server

current_dir = os.path.dirname(__file__)


def test_func(x):
    print(x)


if __name__ == '__main__':
    af = AstraFlux(yaml_file=f'{current_dir}/config.yaml', current_dir=current_dir)

    d = get_current_dir()

    logger = get_logger()
    logger.info(d)
    logger.info(current_dir)
    logger.info(snowflake_id())
    logger.info(get_converted_time())
    logger.info(get_ipaddr())

    # af.registry(services=[test_server, sub_test_server])
    # af.start()

    executor = gen_thread_executor(logger=logger, max_workers=20, retry_delay=1)

    executor.submit(test_func, 1)
    executor.submit(test_func, 2)
    executor.submit(test_func, 3)

    executor.start()
    executor.wait_completion()
    executor.shutdown()

"""
pip install pika
pip install pymongo
pip install redis
pip install pytz
pip install PyYAML
pip install dill
pip install psutil


"""
