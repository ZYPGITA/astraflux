# -*- coding: utf-8 -*-

import os
import json
import asyncio
from openai import AsyncOpenAI
from agents import Agent, Runner, OpenAIChatCompletionsModel

from astraflux.definitions.constants import *
from astraflux.definitions.globals import get_current_dir

# Path of the current script file
script_path = os.path.dirname(os.path.realpath(__file__))


class AstraAgent:

    def __init__(self, logger, config):
        self.logger = logger

        # Directory for temporary files (writable area)
        self.temporary_directory = config.get(
            OpenAI.CONFIG.TEMPORARY_DIRECTORY.value, OpenAI.DEFAULT.TEMPORARY_DIRECTORY.value)

        # Directory for expandable skills (read-only)
        self.expand_skill_directory = config.get(
            OpenAI.CONFIG.EXPAND_SKILL_DIRECTORY.value, OpenAI.DEFAULT.EXPAND_SKILL_DIRECTORY.value)

        # OpenAI.Reasoning server URL
        self.server = config.get(OpenAI.ModelAPI.CONFIG.SERVER.value, OpenAI.ModelAPI.DEFAULT.SERVER.value)

        # Authentication token
        self.api_key = config.get(OpenAI.ModelAPI.CONFIG.APIKEY.value, OpenAI.ModelAPI.DEFAULT.APIKEY.value)
        # model name
        self.model_name = config.get(OpenAI.ModelAPI.CONFIG.NAME.value, OpenAI.ModelAPI.DEFAULT.NAME.value)

        current_dir = get_current_dir()
        self.logger.info(f'current_dir == {current_dir}')

        # Path to built-in system skills (read-only)
        self.system_skill_path = os.path.join(script_path, 'skill')

        # Authorized writable directory – file system rules enforce this
        self.authorization_path = os.path.join(current_dir, self.temporary_directory)
        self.logger.info(f'authorization_path == {self.authorization_path}')

        # Path to expandable skills (read-only)
        self.expand_skill_directory_path = os.path.join(current_dir, self.expand_skill_directory)
        self.logger.info(f'expand_skill_directory_path == {self.expand_skill_directory_path}')

        self.agent = None
        self.tools = []

        self.register_tool()
        self.register_agent()

    def register_tool(self):
        pass

    def register_agent(self):
        client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.server
        )

        model = OpenAIChatCompletionsModel(
            model=self.model_name,
            openai_client=client
        )

        self.agent = Agent(
            name="Astra Ai Agent",
            model=model,
            instructions="你是Astra Ai Agent 你可以连接网络查询数据、调用本地工具、执行命令、创建/修改文件等",
            tools=self.tools
        )


def stream_chat(self, message, prompt=None):
    print(message)


def chat(self, message, prompt=None):
    pass
