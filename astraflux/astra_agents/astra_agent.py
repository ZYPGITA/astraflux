# -*- coding: utf-8 -*-

import os
import json
import inspect
import importlib.util
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

        self.register_system_tools()
        self.register_agent()

    def _import_module_from_path(self, module_name, file_path):
        """Dynamically import a Python module from a file path."""
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            self.logger.warning(f"Could not load spec for {file_path}")
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _find_tool_functions(self, module):
        """Find all FunctionTool instances in a module."""
        from agents.tool import FunctionTool

        tools = []
        for name, obj in inspect.getmembers(module):
            if isinstance(obj, FunctionTool):
                self.logger.debug(f"Found tool: {obj.name} ({name})")
                tools.append(obj)
        return tools

    def register_system_tools(self):
        """
        Scan the system skill directory, dynamically import each .py file,
        discover @function_tool-decorated functions, and register them
        as available tools for the agent.
        """

        if not os.path.isdir(self.system_skill_path):
            self.logger.warning(f"System skill directory not found: {self.system_skill_path}")
            return

        for d in sorted(os.listdir(self.system_skill_path)):
            for f in sorted(os.listdir(os.path.join(self.system_skill_path, d))):
                if not f.endswith('.py') or f == '__init__.py' or f.startswith('_'):
                    continue

                file_path = os.path.join(self.system_skill_path, d, f)
                module_name = f[:-3]

                module = self._import_module_from_path(module_name, file_path)
                if module is None:
                    continue

                found = self._find_tool_functions(module)
                for tool_fn in found:
                    self.tools.append(tool_fn)

        self.logger.info(f"System tool registration complete. Total tools: {len(self.tools)}")

    def register_agent(self):
        client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.server
        )

        model = OpenAIChatCompletionsModel(
            model=self.model_name,
            openai_client=client
        )

        instructions = """You are Astra AI Agent. You can connect to the internet to search for \
        data, call local tools, execute commands, create/modify files, and more. \
        """

        self.agent = Agent(
            name="Astra Ai Agent",
            model=model,
            instructions=instructions,
            tools=self.tools
        )


class AstraAgentApi(AstraAgent):

    async def stream_chat(self, message, prompt=None):
        print(message)
        result_1 = await Runner.run(self.agent, message)
        print(result_1)

    async def chat(self, message, prompt=None):
        pass
