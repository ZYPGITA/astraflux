# -*- encoding: utf-8 -*-

import os
from astraflux import *

current_dir = os.path.dirname(__file__)
af = AstraFlux(yaml_file=f'{current_dir}/config.yaml', current_dir=current_dir)

message = {'task_id': snowflake_id(), 'status': 'wait', 'name': 'xxxx'}


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


# d = proxy_call(
#     service_name='test_server',
#     method_name='test_func',
#     x=1, y=2
# )
# print(d)

# remote_call(
#     service_name='test_service_1',
#     method_name='add_x_y',
#     x=1, y=2
# )

