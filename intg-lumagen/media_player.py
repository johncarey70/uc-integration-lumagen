"""
Media-player entity functions.

:copyright: (c) 2023 by Unfolded Circle ApS.
:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from const import MediaPlayerDef, SimpleCommands
from lumagen import LumagenDevice, LumagenInfo
from ucapi import MediaPlayer, StatusCodes
from ucapi.media_player import (Attributes, Commands, DeviceClasses, Options,
                                States)

_LOG = logging.getLogger(__name__)

class LumagenMediaPlayer(MediaPlayer):
    """Representation of a Lumagen Media Player entity."""

    def __init__(self, mp_info: LumagenInfo, device: LumagenDevice):
        """Initialize the class."""
        self._device = device
        entity_id = f"media_player.{mp_info.id}"
        features = MediaPlayerDef.features
        attributes = MediaPlayerDef.attributes
        self.simple_commands = [*SimpleCommands]

        options = {
            Options.SIMPLE_COMMANDS: self.simple_commands
        }
        super().__init__(
            entity_id,
            mp_info.name,
            features,
            attributes,
            device_class=DeviceClasses.RECEIVER,
            options=options,
        )

        _LOG.debug("LumagenMediaPlayer init %s : %s", entity_id, attributes)

    async def command(self, cmd_id: str, params: dict[str, Any] | None = None) -> StatusCodes:
        """
        Media-player entity command handler.

        Called by the integration-API if a command is sent to a configured media-player entity.

        :param cmd_id: command
        :param params: optional command parameters
        :return: status code of the command request
        """
        _LOG.info("Got %s command request: %s %s", self.id, cmd_id, params)

        match cmd_id:
            case Commands.ON:
                res = await self._device.power_on()
            case Commands.OFF:
                res = await self._device.power_off()
            case Commands.TOGGLE:
                res = await self._device.power_toggle()
            case Commands.SELECT_SOURCE:
                res = await self._device.select_source(params.get("source"))
            case _:
                return StatusCodes.NOT_IMPLEMENTED

        return res

    def filter_changed_attributes(self, update: dict[str, Any]) -> dict[str, Any]:
        """
        Filter the given attributes and return only the changed values.

        :param update: dictionary with attributes.
        :return: filtered entity attributes containing changed attributes only.
        """
        attributes = {}

        for key in (Attributes.STATE, Attributes.SOURCE, Attributes.SOURCE_LIST):
            if key in update and key in self.attributes:
                if update[key] != self.attributes[key]:
                    attributes[key] = update[key]

        if attributes.get(Attributes.STATE) == States:
            attributes[Attributes.SOURCE] = ""

        _LOG.debug("LumagenMediaPlayer update attributes %s -> %s", update, attributes)
        return attributes
