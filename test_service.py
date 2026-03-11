# -*- encoding: utf-8 -*-

import os
import time

from astraflux import *

from servers.test_server import test_server, sub_test_server

current_dir = os.path.dirname(__file__)


def test_func(x):
    while True:
        time.sleep(2)
        print(x)


if __name__ == '__main__':
    af = AstraFlux(yaml_file=f'{current_dir}/config.yaml', current_dir=current_dir)

    d = get_current_dir()

    logger = get_logger()
    logger.info(f'current_dir == {get_current_dir()}')
    logger.info(f'root_path == {get_root_path()}')
    logger.info(snowflake_id())
    logger.info(get_converted_time())
    logger.info(get_ipaddr())

    add_schedule_job(
        job_id='test_001',
        cron_expression='*/10 * * * * *',
        function=test_func,
        keyword_arguments={'x': 2},
        execution_type='thread'  # thread or process
    )

    af.registry(services=[test_server, sub_test_server])
    af.start(wait=False)

    executor = gen_thread_executor(logger=logger, max_workers=20, retry_delay=1)
    executor.submit(test_func, 1)

    executor.start()
    executor.wait_completion()
    executor.shutdown()
