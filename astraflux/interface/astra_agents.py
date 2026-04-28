# -*- coding: utf-8 -*-

from functools import wraps
from astraflux.core import global_manager


def function_tool(func):
    """
    A custom decorator to mark a function as a tool that can be invoked by a Large Language Model (LLM).

    This decorator wraps the original function to preserve its metadata and adds a specific
    attribute to identify it as a callable tool for the AI agent.

    Args:
        func (Callable): The original function to be wrapped.

    Returns:
        Callable: The wrapped function with the '_is_function_tool' attribute set to True.
    """

    # The @wraps decorator from functools is used to copy metadata (like __name__, __doc__)
    # from the original function to the wrapper. This is crucial for the LLM to correctly
    # identify the tool's name and description.
    @wraps(func)
    def wrapper(*args, **kwargs):
        """
        The wrapper function that executes the original function.
        It accepts any number of positional and keyword arguments to ensure flexibility.
        """
        # Execute the original function with the provided arguments and return its result.
        return func(*args, **kwargs)

    # Set a custom attribute to flag this function as a tool.
    # The agent framework can check for this attribute (e.g., if hasattr(func, '_is_function_tool'))
    # to determine which functions are available for the model to call.
    wrapper._is_function_tool = True

    # Return the wrapped function object.
    return wrapper


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
