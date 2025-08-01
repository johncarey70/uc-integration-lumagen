"""
Utility functions for logging setup and command validation in the Lumagen integration.

Includes:
- `setup_logger()`: Dynamically sets logging levels for UC API and related modules based on the
  `UC_LOG_LEVEL` environment variable.
- `validate_simple_commands_exist_on_executor()`: Validates that all commands defined in a given Enum
  are implemented as callables on a specified executor object. Useful for debugging and consistency checks.

These utilities support development and runtime diagnostics in UC API-based Lumagen integrations.
"""


import logging
import os
from enum import Enum
from typing import Type


def setup_logger():
    """Get logger from all modules"""

    level = os.getenv("UC_LOG_LEVEL", "DEBUG").upper()

    logging.getLogger("ucapi.api").setLevel(level)
    logging.getLogger("ucapi.entities").setLevel(level)
    logging.getLogger("ucapi.entity").setLevel(level)
    logging.getLogger("driver").setLevel(level)
    logging.getLogger("config").setLevel(level)
    logging.getLogger("discover").setLevel(level)
    logging.getLogger("setup_flow").setLevel(level)
    logging.getLogger("device").setLevel(level)
    logging.getLogger("remote").setLevel(level)
    logging.getLogger("media_player").setLevel(level)
    logging.getLogger("sensor").setLevel(level)
    #logging.getLogger("pylumagen").setLevel(level)



def validate_simple_commands_exist_on_executor(
    enum_class: Type[Enum],
    executor: object,
    logger: logging.Logger = logging.getLogger(__name__)
) -> list[str]:
    """
    Ensures that each command in the enum resolves to a callable method on the executor,
    using getattr(), which also triggers __getattr__ fallbacks.

    :param enum_class: Enum containing command names.
    :param executor: The CommandExecutor instance.
    :param logger: Logger for output.
    :return: List of commands that failed resolution.
    """
    missing = []

    for cmd in enum_class:
        method_name = cmd.value.lower()
        try:
            method = getattr(executor, method_name)
            if not callable(method):
                missing.append(method_name)
        except AttributeError:
            missing.append(method_name)

    if missing:
        logger.info(
            "Executor missing methods for SimpleCommands: %s", ", ".join(missing)
        )
    else:
        logger.debug("All SimpleCommands are implemented by the executor.")

    return missing
