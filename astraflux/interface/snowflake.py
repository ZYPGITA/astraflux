# -*- encoding: utf-8 -*-

from astraflux.inject import inject_implementation

__all__ = ['snowflake_id']


@inject_implementation()
def snowflake_id() -> str:
    """
    Returns a Snowflake ID generator function.
    Returns:
        function: A function that generates Snowflake IDs.
    """
