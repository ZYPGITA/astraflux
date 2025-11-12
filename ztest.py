# -*- encoding: utf-8 -*-

import os
import time

from astraflux import *

from servers.test_server import test_server

current_dir = os.path.dirname(__file__)

af = AstraFlux(yaml_file=f'{current_dir}/config.yaml', current_dir=current_dir)

d = get_current_dir()

logger = get_logger()
logger.info(d)
logger.info(current_dir)
logger.info(snowflake_id())
logger.info(get_converted_time())
logger.info(get_ipaddr())


af.registry(services=[test_server])
af.run()

time.sleep(1000)


# executor = gen_process_executor(logger=logger, max_workers=20, retry_delay=1)
#
#
# def test_func(x):
#     while True:
#         time.sleep(1)
#         print(x)
#
# executor.submit(test_func, 1)
# executor.submit(test_func, 2)
# executor.submit(test_func, 3)
#
# executor.start()
# executor.wait_completion()
# executor.shutdown()


# task_submit_to_db_and_mq(queue_name='test', task_data={'task_id': snowflake_id()})

#
# print(get_converted_time())
#
# loguru().info(f'current_dir == {current_dir()}')
#
# if __name__ == '__main__':
#     from servers.test_server import test_server
#
#     af.registry(services=[test_server])
#
#     af.start()

"""
pip install pika
pip install pymongo
pip install redis
pip install pytz
pip install PyYAML
pip install dill


"""
