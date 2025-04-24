"""
Defines constant enumerations used for Lumagen remote and media player control.

Includes:
- `SimpleCommands`: Enum mapping human-readable command names to Lumagen-specific remote commands.
  Covers numeric inputs, aspect ratio changes, navigation, power control, and more.
- Designed for use with `ucapi`-based entity integration modules (e.g., remote, media_player).

These constants provide a unified interface for issuing commands across UC integrations.
"""


from enum import Enum

from ucapi import media_player, remote


class SimpleCommands(str, Enum):
    """Enumeration of supported remote command names for Lumagen control."""

    NUM_0 = "send_0"
    NUM_1 = "send_1"
    NUM_2 = "send_2"
    NUM_3 = "send_3"
    NUM_4 = "send_4"
    NUM_5 = "send_5"
    NUM_6 = "send_6"
    NUM_7 = "send_7"
    NUM_8 = "send_8"
    NUM_9 = "send_9"
    NUM_10 = "send_10"
    ASPECT_1_85 = "source_aspect_1_85"
    ASPECT_1_90 = "source_aspect_1_90"
    ASPECT_16_X_9 = "source_aspect_16x9"
    ASPECT_2_00 = "source_aspect_2_00"
    ASPECT_2_10 = "source_aspect_2_10"
    ASPECT_2_20 = "source_aspect_2_20"
    ASPECT_2_35 = "source_aspect_2_35"
    ASPECT_2_40 = "source_aspect_2_40"
    ASPECT_2_55 = "source_aspect_2_55"
    ASPECT_2_76 = "source_aspect_2_76"
    ASPECT_4_X_3 = "source_aspect_4x3"
    AAD = "auto_aspect_disable"
    AAE = "auto_aspect_enable"
    ALT = "alt"
    CLEAR = "clear"
    DOWN = "down"
    EXIT = "exit"
    HDR = "hdr"
    HELP = "help"
    INPUT = "input"
    LBOX = "source_aspect_lbox"
    LEFT = "left"
    MEMA = "mema"
    MEMB = "memb"
    MEMC = "memc"
    MEMD = "memd"
    MENU = "menu"
    MSG_OFF = "clear_message"
    MSG_ON = "display_message"
    NLS = "nls"
    OK = "ok"
    ON = "power_on"
    PATTERN = "pattern"
    PREV = "prev"
    RIGHT = "right"
    SAVE = "save"
    STBY = "standby"
    UP = "up"
    ZONE = "zone"

    @property
    def display_name(self) -> str:
        """
        Returns the display-friendly command name for use in UI or command APIs.
        Normalizes enum member names like NUM_0 ? "0", ASPECT_1_85 ? "1.85", etc.

        :return: A display-safe string.
        """
        name = self.name
        if name.startswith("NUM_"):
            return name[4:]
        if name == "ASPECT_4_X_3":
            return "4x3"
        if name == "ASPECT_16_X_9":
            return "16x9"
        if name.startswith("ASPECT_"):
            return name[7:].replace("_", ".")
        return name


class MediaPlayerDef: # pylint: disable=too-few-public-methods
    """
    Defines a media player entity including supported features, attributes, and
    a list of simple commands.
    """
    features = [
        media_player.Features.ON_OFF,
        media_player.Features.TOGGLE,
        media_player.Features.SELECT_SOURCE,
    ]
    attributes = {
        media_player.Attributes.STATE: media_player.States.UNKNOWN,
        media_player.Attributes.SOURCE: "",
        media_player.Attributes.SOURCE_LIST: [],
    }
    simple_commands = [cmd.display_name for cmd in SimpleCommands]


class RemoteDef: # pylint: disable=too-few-public-methods
    """
    Defines a remote entity including supported features, attributes, and
    a list of simple commands.
    """
    features = [
        remote.Features.ON_OFF,
        remote.Features.TOGGLE,
    ]
    attributes = {
        remote.Attributes.STATE: remote.States.UNKNOWN
    }
    simple_commands = [cmd.display_name for cmd in SimpleCommands]
