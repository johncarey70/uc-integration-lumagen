"""
Media-player entity functions.

:copyright: (c) 2023 by Unfolded Circle ApS.
:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from const import MediaPlayerDef, SimpleCommandMappings
from lumagen import LumagenDevice, LumagenInfo
from ucapi import MediaPlayer, StatusCodes
from ucapi.media_player import Commands, DeviceClasses, Options

_LOG = logging.getLogger(__name__)

class LumagenMediaPlayer(MediaPlayer):
    """Representation of a Lumagen Media Player entity."""

    def __init__(self, mp_info: LumagenInfo, device: LumagenDevice):
        """Initialize the class."""
        self._device = device
        entity_id = f"media_player.{mp_info.id}"
        features = MediaPlayerDef.features
        attributes = MediaPlayerDef.attributes
        self.simple_commands = [*SimpleCommandMappings]

        _LOG.debug("LumagenMediaPlayer init %s : %s", entity_id, attributes)
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
            case Commands.PLAY_PAUSE:
                res = StatusCodes.OK
            case Commands.NEXT:
                res = await self._device.next()
            case Commands.PREVIOUS:
                res = await self._device.previous()
            case Commands.ON:
                res = await self._device.power_on()
            case Commands.OFF:
                res = await self._device.power_off()
            case Commands.TOGGLE:
                res = await self._device.power_toggle()
            case Commands.SELECT_SOURCE:
                res = await self._device.select_source(params.get("source"))
            case Commands.CURSOR_UP:
                res = await self._device.cursor_up()
            case Commands.CURSOR_DOWN:
                res = await self._device.cursor_down()
            case Commands.CURSOR_LEFT:
                res = await self._device.cursor_left()
            case Commands.CURSOR_RIGHT:
                res = await self._device.cursor_right()
            case Commands.CURSOR_ENTER:
                res = await self._device.cursor_enter()
            case Commands.BACK:
                res = await self._device.back()
            case Commands.MENU:
                res = await self._device.setup()
            case Commands.CONTEXT_MENU:
                res = await self._device.options()
            case Commands.INFO:
                res = await self._device.info()
            case cmd if cmd in SimpleCommandMappings:
                res = await self._device.send(SimpleCommandMappings[cmd])
            case _:
                return StatusCodes.NOT_IMPLEMENTED

        return res
