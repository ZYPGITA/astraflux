# -*- encoding: utf-8 -*-

import os

from astraflux import *

os_dir = os.path.dirname(__file__)
af = AstraFlux('config.yaml', os_dir)

print(get_converted_time())

loguru().info(f'current_dir == {current_dir()}')

if __name__ == '__main__':
    from servers.test_server import test_server

    af.registry(services=[test_server])

    af.start()
