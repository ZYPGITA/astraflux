# -*- encoding: utf-8 -*-
import sys

__all__ = ['snowflake_id']


def snowflake_id() -> str:
    """
    Returns a Snowflake ID generator function.
    Returns:
        function: A function that generates Snowflake IDs.
    """
    return sys.modules[__name__].snowflake_id()
