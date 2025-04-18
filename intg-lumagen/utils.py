"""Utils"""

import logging
import os

from ucapi import media_player, remote


def setup_logger():
    """Get logger from all modules"""

    level = os.getenv("UC_LOG_LEVEL", "DEBUG").upper()

    logging.getLogger("ucapi.api").setLevel(level)
    logging.getLogger("ucapi.entities").setLevel(level)
    logging.getLogger("ucapi.entity").setLevel(level)
    logging.getLogger("driver").setLevel(level)
    logging.getLogger("config").setLevel(level)
    logging.getLogger("discover").setLevel(level)
    logging.getLogger("setup").setLevel(level)
    logging.getLogger("lumagen").setLevel(level)
    logging.getLogger("remote").setLevel(level)
    logging.getLogger("media_player").setLevel(level)
    #logging.getLogger("pylumagen").setLevel(level)


def map_state_to_remote(state: media_player.States) -> remote.States:
    """
    Map a media player state to the appropriate remote state.

    This function is used to convert a `States` enum from the media_player domain
    into a `RemoteStates` enum used for the remote entity UI. It ensures consistency
    between media state reporting and remote button state display.

    Note:
        Since `RemoteStates` does not include a distinct STANDBY state,
        STANDBY is mapped to OFF by default.

    Args:
        state (States): The media player state to convert.

    Returns:
        RemoteStates: The corresponding state for the remote entity.
    """
    if state == media_player.States.ON:
        return remote.States.ON
    if state in (media_player.States.STANDBY, media_player.States.OFF):
        return remote.States.OFF
    return remote.States.UNKNOWN
