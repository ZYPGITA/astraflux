# -*- coding: utf-8 -*-

from astraflux.definitions.constants import *

from astraflux.core import global_manager
from astraflux.ai.open_claw import OpenClawChat


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
    _openclaw_config = fixture_config[OpenClaw.CONFIG.KEY.value]
    _logger = fixture_logger.get_logger(PROJECT.NAME.value, OpenClaw.CONFIG.KEY.value)

    _openclaw_producer = OpenClawChat(
        config=_openclaw_config,
        logger=_logger,
    )

    yield _openclaw_producer
