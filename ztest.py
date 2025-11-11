# -*- encoding: utf-8 -*-

import os

from astraflux import *

current_dir = os.path.dirname(__file__)
af = AstraFlux(yaml_file='config.yaml', current_dir=current_dir)

d = get_current_dir()
get_logger().info(d)

print(snowflake_id())

print(get_converted_time())

print(get_ipaddr())

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
