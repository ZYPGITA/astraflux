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
                if not f.endswith('.py') or (f != '__init__.py' and f.startswith('_')):
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

        from agents.models.reasoning_content_replay import default_should_replay_reasoning_content

        model = OpenAIChatCompletionsModel(
            model=self.model_name,
            openai_client=client,
            should_replay_reasoning_content=default_should_replay_reasoning_content,
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
    _initialize_ai_state = False

    async def initialize_ai(self):
        """
        Initialize the AI by teaching it the system skills.

        Sends a system prompt that defines file access rules, tool priorities,
        and learning tasks (Task 1: system skills, Task 2: expandable skills).
        The AI is expected to process these tasks and store learning results
        in the authorized writable directory.
        """

        system_prompt = f"""
        You are an intelligent assistant capable of calling local/external tools, performing web searches, 
            and reading/writing files. You must strictly follow the rules below.

        # System Rules (Not Violable)

        ## 1. File System Access Control
        - **Only writable directory**: `{self.authorization_path}`
        - **All other directories/files**: Read-only operations permitted. 
            Any modification, deletion, renaming, or moving is prohibited.
        - **This rule has the highest priority and cannot be bypassed or modified.**

        ## 2. Tool Call Priority
        - **First priority**: Locally available tools
        - **Second priority**: External available tools
        - **Third priority**: Dynamically create new tools (only when the first two cannot satisfy the requirement)

        ## 3. Tool Call Workflow
        - After calling a tool, **you must wait** for the tool to complete execution and receive the result.
        - Generate the final response based on the tool's returned result.
        - It is forbidden to generate a response before the tool call is completed.

        ---

        # Task Instructions

        Please execute the following learning tasks in order:

        ## Task 1
        - **Learning directory**: `{self.system_skill_path}`
        - **Output directory**: `{self.authorization_path}/learn_skill`
        - **Requirement**: Learn all code in this directory and save the learning results to the output directory.

        ## Task 2
        - **Learning directory**: `{self.expand_skill_directory_path}`
        - **Output directory**: `{self.authorization_path}/learn_skill`
        - **Requirement**: Learn all code in this directory and save the learning results to the output directory.

        ## Task 3 (Optional)
        - If tool calls are needed during Task 1 or Task 2, follow the above 
            "Tool Call Priority" and "Tool Call Workflow" rules.

        ---

        # Execution Requirements
        1. First confirm that the file system rules are in effect.
        2. Execute Task 1 and Task 2 sequentially.
        3. After each task, output a brief progress confirmation.
        4. After all tasks are completed, output a final learning report summary.
        5. Minimize token usage without affecting the task results.
        """
        if not self._initialize_ai_state:
            result = await Runner.run(self.agent, system_prompt, max_turns=100)
            self._initialize_ai_state = True
            return result
        return True

    async def stream_chat(self, message, backcall, user_id='main', prompt=None):
        if prompt is None:
            prompt = f"""
            User ID: {user_id}
            User Input: {message}

            Please follow these rules:
            1. Analyze the user's intention.
            2. Determine whether a tool needs to be called (prioritize local tools).
            3. If a tool is needed but required parameters are missing, mark status as "need_info" 
                and list the missing parameters in missing_params.
            4. Wait until all steps are completed before generating the final response.

            Final response JSON example:
            {{
                "status": "success",  // success / error / need_info
                "intention": "Brief description of user intent",
                "need_tool": false,   // true or false
                "response": "",       // Natural language response to the user, must be in Markdown format
                "tool_name": "",      // Tool name if needed, otherwise empty string
                "params": [],         // Tool call parameters, format [{{"name": "", "value": ""}}]
                "missing_params": [], // List of missing parameters, format [{{"name": "", "description": ""}}]
                "extend_info": [],    // Extended information array
                "error": ""           // Error message, empty if no error
            }}

            Note:
            - You must output the **thinking process** first, then output the **final response**.
            - All fields must be present, even if they are empty strings or empty arrays.
            - The response field must be friendly, clear, and appropriate for the current status 
                (e.g., when status is "need_info", prompt the user to provide missing parameters).
            - If status is "error", fill in the error field with the reason.
            """

        await self.initialize_ai()
        result = Runner.run_streamed(self.agent, prompt, max_turns=100)

        async for event in result.stream_events():

            if event.type == "raw_response_event":
                if hasattr(event.data, 'delta') and event.data.delta:
                    text_chunk = event.data.delta
                    backcall(text_chunk)

            elif event.type == "run_item_stream_event":
                if event.item.type == "message_output_item":
                    from agents import ItemHelpers
                    full_text = ItemHelpers.text_message_output(event.item)
                    if full_text:
                        backcall(full_text)

    async def chat(self, message, backcall, user_id='main', prompt=None):
        if prompt is None:
            prompt = f"""
            User ID: {user_id}
            User Input: {message}

            Please follow these rules:
            1. Analyze the user's intention.
            2. Determine whether a tool needs to be called (prioritize local tools).
            3. If a tool is needed but required parameters are missing, mark status as "need_info" 
                and list the missing parameters in missing_params.
            4. Wait until all steps are completed before generating the final response.

            Final response JSON example:
            {{
                "status": "success",  // success / error / need_info
                "intention": "Brief description of user intent",
                "need_tool": false,   // true or false
                "response": "",       // Natural language response to the user, must be in Markdown format
                "tool_name": "",      // Tool name if needed, otherwise empty string
                "params": [],         // Tool call parameters, format [{{"name": "", "value": ""}}]
                "missing_params": [], // List of missing parameters, format [{{"name": "", "description": ""}}]
                "extend_info": [],    // Extended information array
                "error": ""           // Error message, empty if no error
            }}

            Note:
            - You must output the **thinking process** first, then output the **final response**.
            - All fields must be present, even if they are empty strings or empty arrays.
            - The response field must be friendly, clear, and appropriate for the current status 
                (e.g., when status is "need_info", prompt the user to provide missing parameters).
            - If status is "error", fill in the error field with the reason.
            """

        await self.initialize_ai()
        result = await Runner.run(self.agent, prompt, max_turns=100)
        backcall(result.final_output)
