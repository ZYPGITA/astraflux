# -*- encoding: utf-8 -*-

import os
from astraflux import *

os_dir = os.path.dirname(__file__)
af = AstraFlux('config.yaml', os_dir)

loguru().info(f'current_dir == {current_dir()}')

if __name__ == '__main__':
    for i in range(1):
        message = {'task_id': snowflake_id(), 'status': TASK.KEY_TASK_STOP_STATUS, 'name': 'xxxx'}
        task_submit_databases(queue='test_server', message=message)

    d = proxy_call(
        service_name='test_server',
        method_name='test_func',

        # 函数入参
        a=1, b=2
    )
    print(d)
