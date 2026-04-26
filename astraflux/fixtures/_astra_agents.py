# -*- coding: utf-8 -*-

from astraflux.definitions.constants import *

from astraflux.core import global_manager
from astraflux.astra_agents.open_claw import OpenClawChat
from astraflux.astra_agents.astra_agent import AstraAgent


@global_manager.register_fixture(name="fixture_openclaw", scope=Scope.GLOBAL)
def _openclaw(fixture_config, fixture_logger):
    """
    Fixture factory for OpenClawChat.

    This function is registered with the global manager to create and provide
    an OpenClawChat instance. It extracts the OpenClaw configuration from the
    fixture_config, creates a logger, initializes the OpenClawChat, and yields
    it as a fixture for dependency injection.

    Args:
        fixture_config (dict): Global configuration containing the "openclaw" key.
        fixture_logger: Logger factory for creating component-specific loggers.

    Yields:
        OpenClawChat: An initialized OpenClawChat instance.
    """
    _openai_config = fixture_config[OpenAI.CONFIG.KEY.value]
    _openclaw_config = _openai_config[OpenAI.OpenClaw.CONFIG.KEY.value]
    _logger = fixture_logger.get_logger(PROJECT.NAME.value, OpenAI.OpenClaw.CONFIG.KEY.value)

    _openclaw_producer = OpenClawChat(
        config=_openclaw_config,
        logger=_logger,
    )

    yield _openclaw_producer


@global_manager.register_fixture(name="fixture_astra_agent", scope=Scope.GLOBAL)
def _astra_agent(fixture_config, fixture_logger):
    """
    Retrieves the AstraAgent object. The agent provides two primary functions for AI interaction:
    streaming dialogue and standard non-streaming responses.

    Available methods:
        - stream_chat(self, message, prompt=None): Handles real-time streaming interactions.
        - chat(self, message, prompt=None): Handles standard, non-streaming request-response cycles.
    """
    _openai_config = fixture_config[OpenAI.CONFIG.KEY.value]
    _agent_config = _openai_config[OpenAI.ModelAPI.CONFIG.KEY.value]
    _logger = fixture_logger.get_logger(PROJECT.NAME.value, OpenAI.ModelAPI.CONFIG.KEY.value)

    _agent_producer = AstraAgent(
        config=_agent_config,
        logger=_logger,
    )

    yield _agent_producer
