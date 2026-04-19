# -*- coding: utf-8 -*-


import sys
import argparse
from flask_cors import CORS
from flask import Flask, request, jsonify

from astraflux import AstraFlux
from astraflux.definitions.constants import *


class WebApp:
    """Flask Web Application"""

    def __init__(self, logger_instance, config: dict):
        self.logger = logger_instance
        self.config = config

        self.port = config.get(WEB.CONFIG.PORT.value, WEB.DEFAULT.PORT.value)
        self.bind_ip = config.get(WEB.CONFIG.BIND_IP.value, WEB.DEFAULT.BIND_IP.value)
        self.username = config.get(WEB.CONFIG.USERNAME.value, WEB.DEFAULT.USERNAME.value)
        self.password = config.get(WEB.CONFIG.PASSWORD.value, WEB.DEFAULT.PASSWORD.value)

        self.app = Flask(__name__)

    def index(self):
        """
        首页,如果未登录调转到登录
        """

    def login(self):
        """
        登录
        """

    def logout(self):
        """
        退出登录
        """

    def query_server_list(self):
        """
        获取服务列表
        """

    def update_max_process(self):
        """
        更新 max_process
        """

    def query_task_list(self):
        """
        获取任务列表
        """

    def retry_task(self):
        """
        任务重试， 更新任务状态即可
        """

    def forced_termination_task(self):
        """
        强制终止正在运行的任务
        """

    def web_launch(self):
        pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Distributed App Component Launcher")

    # Define command line arguments
    parser.add_argument("--yaml_file", type=str, required=True,
                        help="Path to YAML configuration file")
    parser.add_argument("--class_path", type=str, required=True,
                        help="Path to service class definition file")
    parser.add_argument("--current_dir", type=str, required=True,
                        help="Current working directory")

    # Parse arguments
    args = parser.parse_args()
    # Add current directory to Python path for module discovery
    sys.path.append(args.current_dir)

    AstraFlux(yaml_path=args.yaml_file, current_dir=args.current_dir)

    from astraflux.interface.logger import logger
    from astraflux.interface.other import config_obj

    _logger = logger(dirname=PROJECT.NAME.value, filename=WEB.CONFIG.KEY.value)
    _config = config_obj().get(WEB.CONFIG.KEY.value)
    WebApp(logger_instance=logger, config=_config).web_launch()
