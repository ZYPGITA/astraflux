# -*- coding: utf-8 -*-

from astraflux.core import global_manager


def send_message_to_openclaw(user_message: str, user_id='main', prompt=None):
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

    def _backcall(fixture_openclaw):
        return fixture_openclaw.send_message_to_openclaw(user_message=user_message, user_id=user_id, prompt=prompt)

    return global_manager.bind_fixture_func(_backcall)()


def astra_agent():
    """
    Retrieves the AstraAgent object. The agent provides two primary functions for AI interaction:
    streaming dialogue and standard non-streaming responses.

    Available methods:
        - stream_chat(message:str, prompt:str=None): Handles real-time streaming interactions.
        - chat(message:str, prompt:str=None): Handles standard, non-streaming request-response cycles.
    """

    def _backcall(fixture_astra_agent):
        return fixture_astra_agent

    return global_manager.bind_fixture_func(_backcall)()
