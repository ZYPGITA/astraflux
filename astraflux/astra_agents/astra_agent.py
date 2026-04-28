# -*- coding: utf-8 -*-

import os
import json
import inspect
import importlib.util

from openai import AsyncOpenAI
from typing import Dict, List, Callable

from astraflux.definitions.constants import *
from astraflux.definitions.globals import get_current_dir

# Path of the current script file
script_path = os.path.dirname(os.path.realpath(__file__))


class AstraNativeAgent:
    """
    A native AI agent implementation using the OpenAI SDK directly.

    This agent provides tool registration, conversation history management,
    and automatic handling of tool calls without relying on third-party agent frameworks.
    It supports both synchronous and asynchronous tool execution.
    """

    def __init__(self, logger, config):
        """
        Initialize the AstraNativeAgent with configuration and logger.

        Args:
            logger: Logger instance for recording events and errors
            config: Configuration dictionary containing API settings, directories, and model parameters
        """
        self.logger = logger
        self.tools: Dict[str, Callable] = {}
        """Dictionary mapping tool names to their callable functions."""

        self.tools_schema: List[dict] = []
        """List of OpenAI-compatible tool schemas for API requests."""

        # Directory for temporary files (writable area)
        self.temporary_directory = config.get(
            OpenAI.CONFIG.TEMPORARY_DIRECTORY.value, OpenAI.DEFAULT.TEMPORARY_DIRECTORY.value)

        # Directory for expandable skills (read-only)
        self.expand_skill_directory = config.get(
            OpenAI.CONFIG.EXPAND_SKILL_DIRECTORY.value, OpenAI.DEFAULT.EXPAND_SKILL_DIRECTORY.value)

        # OpenAI API server URL
        self.server = config.get(OpenAI.ModelAPI.CONFIG.SERVER.value, OpenAI.ModelAPI.DEFAULT.SERVER.value)

        # Authentication token for API access
        self.api_key = config.get(OpenAI.ModelAPI.CONFIG.APIKEY.value, OpenAI.ModelAPI.DEFAULT.APIKEY.value)

        # Model name to use for chat completions
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

        self.conversation_history = {}

        """List of messages in the current conversation session."""

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.server
        )
        """Async OpenAI client for API communication."""

        self.system_prompt = """You are Astra AI Agent. You can connect to the internet to search for 
        data, call local tools, execute commands, create/modify files, and more.

        When you need to use a tool, respond with a function call. 
        After receiving tool results, provide a natural language response to the user.
        """
        """System prompt defining agent behavior and capabilities."""

        self.logger.info(f"Native agent initialized with model: {self.model_name}")

        self.register_system_tools()

    def register_tool(self, func: Callable = None, *, name: str = None, description: str = None):
        """
        Register a function as a tool that the agent can call.

        Can be used as a decorator or called directly.

        Args:
            func: The function to register as a tool
            name: Optional custom name for the tool (defaults to function name)
            description: Optional description of the tool (defaults to function docstring)

        Returns:
            The decorated function

        Raises:
            Exception: If no function is provided when used as a direct call

        Example:
            @agent.register_tool
            def get_weather(city: str) -> str:
                '''Get weather for a city'''
                return f"Weather in {city}: Sunny"
        """

        def decorator(f):
            tool_name = name or f.__name__
            tool_desc = description or (f.__doc__ or "").strip()

            # Extract function signature to build parameter schema
            sig = inspect.signature(f)
            parameters = {
                "type": "object",
                "properties": {},
                "required": []
            }

            for param_name, param in sig.parameters.items():
                # Map Python types to JSON Schema types
                param_type = "string"
                if param.annotation != inspect.Parameter.empty:
                    if param.annotation == int:
                        param_type = "integer"
                    elif param.annotation == float:
                        param_type = "number"
                    elif param.annotation == bool:
                        param_type = "boolean"
                    elif param.annotation == list:
                        param_type = "array"
                    elif param.annotation == dict:
                        param_type = "object"

                parameters["properties"][param_name] = {
                    "type": param_type,
                    "description": f"Parameter {param_name}"
                }
                if param.default == inspect.Parameter.empty:
                    parameters["required"].append(param_name)

            # Store the function in tools dictionary
            self.tools[tool_name] = f

            # Build OpenAI-compatible tool schema
            tool_schema = {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": tool_desc,
                    "parameters": parameters
                }
            }
            self.tools_schema.append(tool_schema)
            return f

        if func is None:
            raise Exception("You must provide a function")

        return decorator(func)

    def register_tool_from_file(self, file_path: str) -> bool:
        """
        Dynamically import a Python file and register all @function_tool decorated functions.

        Args:
            file_path: Path to the Python file containing tool functions

        Returns:
            True if registration succeeded, False otherwise
        """
        if not os.path.isfile(file_path):
            self.logger.warning(f"Tool file not found: {file_path}")
            return False

        module_name = os.path.basename(file_path).replace('.py', '')

        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                return False

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Scan module for functions marked with _is_function_tool attribute
            for name, obj in inspect.getmembers(module):
                if hasattr(obj, '_is_function_tool'):
                    self.register_tool(obj, name=obj.__name__, description=obj.__doc__)
                    self.logger.debug(f"Imported tool: {obj.__name__}")

            return True
        except Exception as e:
            self.logger.error(f"Failed to import {file_path}: {e}")
            return False

    def register_system_tools(self):
        """
        Batch register all tools from the system skills directory.

        Recursively walks through the system_skill_path directory and registers
        all __init__.py files containing @function_tool decorated functions.
        """
        if not os.path.isdir(self.system_skill_path):
            self.logger.warning(f"System skill directory not found: {self.system_skill_path}")
            return

        for root, dirs, files in os.walk(self.system_skill_path):
            for f in files:
                if f == '__init__.py':
                    file_path = os.path.join(root, f)
                    self.register_tool_from_file(file_path)

        self.logger.info(f"System tool registration complete. Total tools: {len(self.tools)}")

    async def _execute_tool(self, tool_name: str, arguments: dict) -> str:
        """
        Execute a registered tool with the given arguments.

        Args:
            tool_name: Name of the tool to execute
            arguments: Dictionary of arguments to pass to the tool function

        Returns:
            JSON string containing the tool execution result or error message
        """
        if tool_name not in self.tools:
            error_msg = f"Tool '{tool_name}' not found"
            self.logger.error(error_msg)
            return json.dumps({"error": error_msg})

        try:
            func = self.tools[tool_name]
            result = func(**arguments)

            # Handle async functions that return coroutines
            if inspect.iscoroutine(result):
                result = await result

            # Serialize result to JSON string
            if isinstance(result, (str, int, float, bool, list, dict)):
                return json.dumps(result, ensure_ascii=False) if not isinstance(result, str) else result
            else:
                return str(result)
        except Exception as e:
            error_msg = f"Tool execution error: {e}"
            self.logger.error(error_msg)
            return json.dumps({"error": error_msg})

    async def _handle_tool_calls(self, tool_calls: list) -> List[dict]:
        """
        Process multiple tool calls from the assistant's response.

        Args:
            tool_calls: List of tool call objects from the API response

        Returns:
            List of tool result messages formatted for API consumption
        """
        tool_results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            self.logger.info(f"Calling tool: {tool_name}, args: {arguments}")
            result = await self._execute_tool(tool_name, arguments)
            tool_results.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })
        return tool_results

    def reset_conversation(self):
        """
        Reset the conversation history.

        Clears all stored messages from the current conversation session.
        """
        self.conversation_history = []
        self.logger.info("Conversation history reset")

    def add_to_history(self, user_id: str, role: str, content: str):
        """
        Manually add a message to the conversation history.

        Args:
            user_id: User ID of the user to add the message to
            role: Message role ('user', 'assistant', or 'system')
            content: Message content text
        """
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []

        self.conversation_history[user_id].append({"role": role, "content": content})


class AstraAgentApi(AstraNativeAgent):
    """
    API wrapper class for AstraNativeAgent.

    This class inherits all functionality from AstraNativeAgent and can be extended
    with additional API-specific features like session management, authentication,
    or request/response formatting.
    """

    __initialize_ai_state = False

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

    @staticmethod
    def prompt(prompt: str, user_id: str, message: str) -> str:
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

        return prompt

    async def chat(self, message: str, backcall: Callable = None,
                   user_id: str = 'main', temperature: float = 1.0, prompt: str = None) -> str:
        """
        Send a message to the agent and get a response with automatic tool handling.

        This method handles the full conversation loop including:
        - Maintaining conversation history
        - Automatic tool call detection and execution
        - Multi-turn tool usage (handling tool results and continuing)

        Args:
            message: User's input message
            backcall: Optional callback function for streaming/real-time output
            user_id: User identifier for session management (reserved for future use)
            temperature: Sampling temperature (0.0 to 2.0, higher = more creative)
            prompt: prompt

        Returns:
            The assistant's final response text
        """
        _prompt = self.prompt(prompt, user_id, message)

        # Build message list with system prompt and conversation history
        messages = [
            {"role": "system", "content": self.system_prompt},
            *self.conversation_history,
            {"role": "user", "content": _prompt}
        ]

        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []

        conversation_history = self.conversation_history[user_id]

        # Add user message to conversation history
        conversation_history.append({"role": "user", "content": message})

        max_iterations = 10

        for iteration in range(max_iterations):
            extra_body = {}

            # Make API call with current message state
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=self.tools_schema if self.tools_schema else None,
                tool_choice="auto" if self.tools_schema else None,
                temperature=temperature,
                extra_body=extra_body if extra_body else None
            )

            assistant_message = response.choices[0].message

            response_text = assistant_message.content or ""

            # Extract reasoning_content if present (for models that support thinking)
            reasoning = getattr(assistant_message, 'reasoning_content', None) or (
                getattr(assistant_message, 'additional_kwargs', {}).get('reasoning_content'))

            # Handle tool calls if present
            if assistant_message.tool_calls:
                # Build assistant message entry with tool calls
                assistant_entry = {
                    "role": "assistant",
                    "content": response_text,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in assistant_message.tool_calls
                    ]
                }

                # Preserve reasoning_content if it exists
                if reasoning:
                    assistant_entry["reasoning_content"] = reasoning

                # Add assistant message to history
                conversation_history.append(assistant_entry)

                # Execute all tool calls
                tool_results = await self._handle_tool_calls(assistant_message.tool_calls)

                # Rebuild messages including tool results for next iteration
                messages = [
                    {"role": "system", "content": self.system_prompt},
                    *self.conversation_history,
                    *tool_results
                ]

                # Add tool results to conversation history
                conversation_history.extend(tool_results)
                continue  # Continue loop to allow assistant to process tool results

            # No tool calls - return the final response
            if response_text:
                assistant_entry = {"role": "assistant", "content": response_text}

                # Preserve reasoning_content if it exists
                if reasoning:
                    assistant_entry["reasoning_content"] = reasoning

                # Add assistant response to history
                conversation_history.append(assistant_entry)

                # Call backcall if provided
                if backcall:
                    backcall(response_text)
                return response_text
            else:
                # Empty response - return empty string
                return ""

        return "Max iterations reached without final response"
