"""Constants."""

from enum import Enum

from ucapi import media_player, remote


class SimpleCommands(str, Enum):
    """
    Enumeration of supported remote command names for Lumagen control,
    along with their RS-232 ASCII mapping.
    """

    # (value, ascii mapping)
    ALT = ("ALT", ":")
    CLEAR = ("CLEAR", "!")
    DOWN = ("DOWN", "v")
    EXIT = ("EXIT", "X")
    HELP = ("HELP", "U")
    INPUT = ("INPUT", "i")
    LEFT = ("LEFT", "<")
    MENU = ("MENU", "M")
    OK = ("OK", "k")
    ON = ("ON", "%")
    PREV = ("PREV", "P")
    RIGHT = ("RIGHT", ">")
    STBY = ("STBY", "$")
    UP = ("UP", "^")

    MEMA = ("MEMA", "a")
    MEMB = ("MEMB", "b")
    MEMC = ("MEMC", "c")
    MEMD = ("MEMD", "d")

    AAE = ("AAE", "?")
    AAD = ("AAD", "V")
    SAVE = ("SAVE", "S")

    A1_85 = ("1.85", "j")
    A1_90 = ("1.90", "A")
    A2_00 = ("2.00", "C")
    A2_10 = ("2.10", "+j")
    A2_20 = ("2.20", "E")
    A2_35 = ("2.35", "W")
    A2_40 = ("2.40", "G")
    A2_55 = ("2.55", "+W")
    A2_76 = ("2.76", "+N")
    A4_3 = ("4:3", "n")
    A16_9 = ("16:9", "w")
    LBOX = ("LBOX", "l")

    HDR = ("HDR", "Y")
    NLS = ("NLS", "N")
    PATTERN = ("PATTERN", "H")
    ZONE = ("ZONE", "L")
    MSG_ON = ("MSG_ON", "g")
    MSG_OFF = ("MSG_OFF", "s")

    NUM_0 = ("0", None)
    NUM_1 = ("1", None)
    NUM_2 = ("2", None)
    NUM_3 = ("3", None)
    NUM_4 = ("4", None)
    NUM_5 = ("5", None)
    NUM_6 = ("6", None)
    NUM_7 = ("7", None)
    NUM_8 = ("8", None)
    NUM_9 = ("9", None)
    NUM_10 = ("10", "+")

    def __new__(cls, value, ascii_code=None):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj._ascii = ascii_code
        return obj

    @property
    def ascii(self) -> str | None:
        """Returns the RS-232 ASCII mapping for the command, if available."""
        return self._ascii

SimpleCommandMappings = {cmd.value: cmd.ascii for cmd in SimpleCommands if cmd.ascii is not None}


class MediaPlayerDef: # pylint: disable=too-few-public-methods
    """
    Defines a media player entity including supported features, attributes, and
    a list of simple commands.
    """
    features = [
        media_player.Features.ON_OFF,
        media_player.Features.TOGGLE,
        media_player.Features.PLAY_PAUSE,
        media_player.Features.SELECT_SOURCE,
    ]
    attributes = {
        media_player.Attributes.STATE: media_player.States.UNKNOWN,
        media_player.Attributes.SOURCE: "HDMI1",
        media_player.Attributes.SOURCE_LIST: ["HDMI1", "HDMI2"],
    }
    simple_commands = list(SimpleCommandMappings)


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
    simple_commands = list(SimpleCommandMappings)
