# -*- coding: utf-8 -*-

import os
import json
import requests

from astraflux.definitions.constants import *
from astraflux.definitions.globals import get_current_dir

# Path of the current script file
script_path = os.path.dirname(os.path.realpath(__file__))


class OpenClawChat:
    """
    OpenClaw Chat Client

    Manages communication with the OpenClaw AI server, handles system prompts,
    skill learning tasks, and streaming chat interactions.
    """

    def __init__(self, logger, config):
        """
        Initialize the OpenClaw chat client.

        Args:
            logger: Logger instance for recording events and errors.
            config (dict): Configuration dictionary containing server, token,
                           session key, and directory settings.
        """
        self.logger = logger

        # Directory for temporary files (writable area)
        self.temporary_directory = config.get(
            OpenClaw.CONFIG.TEMPORARY_DIRECTORY.value, OpenClaw.DEFAULT.TEMPORARY_DIRECTORY.value)

        # Directory for expandable skills (read-only)
        self.expand_skill_directory = config.get(
            OpenClaw.CONFIG.EXPAND_SKILL_DIRECTORY.value, OpenClaw.DEFAULT.EXPAND_SKILL_DIRECTORY.value)

        # OpenClaw server URL
        self.server = config.get(OpenClaw.CONFIG.SERVER.value, OpenClaw.DEFAULT.SERVER.value)

        # Authentication token
        self.token = config.get(OpenClaw.CONFIG.TOKEN.value, OpenClaw.DEFAULT.TOKEN.value)
        # Session key for the conversation
        self.session_key = config.get(OpenClaw.CONFIG.SESSION_KEY.value, OpenClaw.DEFAULT.SESSION_KEY.value)

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

        # HTTP headers for API requests
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            'x-openclaw-session-key': self.session_key
        }

        # OpenClaw chat completion endpoint
        self.baseurl = f'{self.server}/v1/chat/completions'

        # Initialize the AI by sending the system learning tasks
        self.initialize_ai()

    def stream_chat(self, payload):
        """
        Send a chat request with streaming enabled and yield response chunks.

        Args:
            payload (dict): The JSON payload for the chat completion request.

        Yields:
            str: Content chunks from the streaming response.

        Raises:
            requests.exceptions.HTTPError: If the request fails.
        """
        response = requests.post(self.baseurl, headers=self.headers, json=payload, stream=True)
        response.raise_for_status()

        # Process each line of the streaming response
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith('data:'):
                    # Extract JSON after 'data: ' prefix
                    json_data = decoded_line.replace('data: ', '', 1)
                    if json_data.strip() == '[DONE]':
                        break
                    try:
                        chunk = json.loads(json_data)
                        content = chunk['choices'][0]['delta'].get('content', '')
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        # Skip malformed JSON chunks
                        pass

    def initialize_ai(self):
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

        self.logger.debug(system_prompt)

        # Create a payload that sends the system prompt as both system and user message
        # to ensure the AI fully processes the learning tasks.
        payload = {
            "model": "openclaw:main",
            "stream": True,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": system_prompt}
            ]
        }

        # Stream the response and collect the full output
        item = self.stream_chat(payload=payload)

        full_response = ''
        for i in item:
            full_response += i

        self.logger.debug(full_response)
        self.logger.info("system learn done")

    def send_message_to_openclaw(self, user_message: str, user_id='main', prompt=None):
        """
        Send a user message to OpenClaw and return a streaming response.

        The method constructs a prompt (or uses a provided one) that instructs
        the AI to analyze intent, decide on tool usage, handle missing parameters,
        and output a JSON response with a preceding thinking process.

        Args:
            user_message (str): The user's input message.
            user_id (str): Identifier for the user (default 'main').
            prompt (str, optional): Custom prompt to override the default.

        Returns:
            generator: A generator yielding content chunks from the streaming response.
        """
        if prompt is None:
            prompt = f"""
            User ID: {user_id}
            User Input: {user_message}

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

        payload = {
            "model": "openclaw:main",
            "stream": True,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        return self.stream_chat(payload=payload)
