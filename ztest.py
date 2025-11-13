# -*- encoding: utf-8 -*-

import os
import time

from astraflux import *

from servers.test_server import test_server, sub_test_server

current_dir = os.path.dirname(__file__)

af = AstraFlux(yaml_file=f'{current_dir}/config.yaml', current_dir=current_dir)

d = get_current_dir()

logger = get_logger()
logger.info(d)
logger.info(current_dir)
logger.info(snowflake_id())
logger.info(get_converted_time())
logger.info(get_ipaddr())

af.registry(services=[test_server, sub_test_server])
af.start()

executor = gen_process_executor(logger=logger, max_workers=20, retry_delay=1)

# add_schedule_job(
#     job_id='1001',
#     cron_expression='* * * * * *',
#     function=test_func_2,
#     keyword_arguments={'x': 2}
# )

# start_scheduler()

# for i in range(3):
#     tid = snowflake_id()
#
#     task_submit_to_db(
#         queue_name='test_server',
#         task_data={'task_id': tid}
#     )
#
#     subtask_batch_create(
#         source_task_id=tid,
#         subtask_queue='sub_test_server',
#         subtask_list=[{'task_id': f'{tid}_{j}'} for j in range(5)]
#     )
#
# time.sleep(10)
# from astraflux.workflows.task_distribution import TaskScheduler
#
# TaskScheduler().execute()
#
time.sleep(100)

# executor.submit(test_func, 1)
# executor.submit(test_func, 2)
# executor.submit(test_func, 3)
#
# executor.start()
# executor.wait_completion()
# executor.shutdown()


"""
pip install pika
pip install pymongo
pip install redis
pip install pytz
pip install PyYAML
pip install dill
pip install psutil


"""
