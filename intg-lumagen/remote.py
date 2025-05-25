"""
Remote entity functions.

:copyright: (c) 2023 by Unfolded Circle ApS.
:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import asyncio
import logging
from typing import Any

from const import RemoteDef
from const import SimpleCommands as cmds
from lumagen import LumagenDevice, LumagenInfo
from ucapi import Remote, StatusCodes, remote
from ucapi.media_player import Attributes as MediaAttributes
from ucapi.media_player import States as MediaStates
from ucapi.remote import Attributes, Commands, States
from ucapi.ui import (Buttons, DeviceButtonMapping, Size, UiPage,
                      create_btn_mapping, create_ui_icon, create_ui_text)

_LOG = logging.getLogger(__name__)

REMOTE_STATE_MAPPING = {
    MediaStates.OFF: States.OFF,
    MediaStates.ON: States.ON,
    MediaStates.STANDBY: States.OFF,
    MediaStates.UNAVAILABLE: States.UNAVAILABLE,
    MediaStates.UNKNOWN: States.UNKNOWN,
}

class LumagenRemote(Remote):
    """Representation of a Lumagen Remote entity."""

    def __init__(self, info: LumagenInfo, device: LumagenDevice):
        """Initialize the class."""
        self._device = device
        entity_id = f"remote.{info.id}"
        features = RemoteDef.features
        attributes = RemoteDef.attributes
        super().__init__(
            entity_id,
            f"Intg-{info.name}",
            features,
            attributes,
            simple_commands=RemoteDef.simple_commands,
            button_mapping=self.create_button_mappings(),
            ui_pages=self.create_ui()
        )


        _LOG.debug("LumagenRemote init %s : %s", entity_id, attributes)


    def create_button_mappings(self) -> list[DeviceButtonMapping | dict[str, Any]]:
        """Create button mappings."""
        return [
            create_btn_mapping(Buttons.DPAD_UP, cmds.UP.value),
            create_btn_mapping(Buttons.DPAD_DOWN, cmds.DOWN.value),
            create_btn_mapping(Buttons.DPAD_LEFT, cmds.LEFT.value),
            create_btn_mapping(Buttons.DPAD_RIGHT, cmds.RIGHT.value),
            create_btn_mapping(Buttons.DPAD_MIDDLE, cmds.OK.value),
            create_btn_mapping(Buttons.PREV, cmds.PREV.value),
            create_btn_mapping(Buttons.NEXT, cmds.ALT.value),

            {"button": "POWER", "short_press": {"cmd_id": "remote.toggle"}},
            {"button": "MENU", "short_press": {"cmd_id": cmds.MENU.value}},
        ]

    def create_ui(self) -> list[UiPage | dict[str, Any]]:
        """Create a user interface with different pages that includes all commands"""

        ui_page1 = UiPage("page1", "Power & Input", grid=Size(6, 6))
        ui_page1.add(create_ui_text("Power On", 2, 0, size=Size(6, 1), cmd=send_cmd(Commands.ON)))
        ui_page1.add(create_ui_text("1", 0, 1, size=Size(2, 1), cmd=send_cmd(cmds.NUM_1)))
        ui_page1.add(create_ui_text("2", 2, 1, size=Size(2, 1), cmd=send_cmd(cmds.NUM_2)))
        ui_page1.add(create_ui_text("3", 4, 1, size=Size(2, 1), cmd=send_cmd(cmds.NUM_3)))
        ui_page1.add(create_ui_text("4", 0, 2, size=Size(2, 1), cmd=send_cmd(cmds.NUM_4)))
        ui_page1.add(create_ui_text("5", 2, 2, size=Size(2, 1), cmd=send_cmd(cmds.NUM_5)))
        ui_page1.add(create_ui_text("6", 4, 2, size=Size(2, 1), cmd=send_cmd(cmds.NUM_6)))
        ui_page1.add(create_ui_text("7", 0, 3, size=Size(2, 1), cmd=send_cmd(cmds.NUM_7)))
        ui_page1.add(create_ui_text("8", 2, 3, size=Size(2, 1), cmd=send_cmd(cmds.NUM_8)))
        ui_page1.add(create_ui_text("9", 4, 3, size=Size(2, 1), cmd=send_cmd(cmds.NUM_9)))
        ui_page1.add(create_ui_text("10+", 0, 4, size=Size(2, 1), cmd=send_cmd(cmds.NUM_10)))
        ui_page1.add(create_ui_text("0", 2, 4, size=Size(2, 1), cmd=send_cmd(cmds.NUM_0)))
        ui_page1.add(create_ui_text("Input", 4, 4, size=Size(2, 1), cmd=send_cmd(cmds.INPUT)))
        ui_page1.add(create_ui_text("Standby", 0, 5, size=Size(6, 1), cmd=Commands.OFF))

        ui_page2 = UiPage("page2", "Source Aspect Ratios", grid=Size(6, 6))
        ui_page2.add(create_ui_text("4:3", 0, 0, size=Size(2, 1), cmd=send_cmd(cmds.ASPECT_4_X_3)))
        ui_page2.add(create_ui_text("Lbox", 2, 0, size=Size(2, 1), cmd=send_cmd(cmds.LBOX)))
        ui_page2.add(create_ui_text("16:9", 4, 0, size=Size(2, 1), cmd=send_cmd(cmds.ASPECT_16_X_9)))
        ui_page2.add(create_ui_text("1.85", 0, 1, size=Size(2, 1), cmd=send_cmd(cmds.ASPECT_1_85)))
        ui_page2.add(create_ui_text("1.90", 2, 1, size=Size(2, 1), cmd=send_cmd(cmds.ASPECT_1_90)))
        ui_page2.add(create_ui_text("2.00", 4, 1, size=Size(2, 1), cmd=send_cmd(cmds.ASPECT_2_00)))
        ui_page2.add(create_ui_text("2.10", 0, 2, size=Size(2, 1), cmd=send_cmd(cmds.ASPECT_2_10)))
        ui_page2.add(create_ui_text("2.20", 2, 2, size=Size(2, 1), cmd=send_cmd(cmds.ASPECT_2_20)))
        ui_page2.add(create_ui_text("2.35", 4, 2, size=Size(2, 1), cmd=send_cmd(cmds.ASPECT_2_35)))
        ui_page2.add(create_ui_text("2.40", 0, 3, size=Size(2, 1), cmd=send_cmd(cmds.ASPECT_2_40)))
        ui_page2.add(create_ui_text("2.55", 2, 3, size=Size(2, 1), cmd=send_cmd(cmds.ASPECT_2_55)))
        ui_page2.add(create_ui_text("NLS", 4, 3, size=Size(2, 1), cmd=send_cmd(cmds.NLS)))
        ui_page2.add(create_ui_text("-- Auto Aspect --", 0, 4, size=Size(6, 1)))
        ui_page2.add(create_ui_text("Enable", 0, 5, size=Size(3, 1), cmd=send_cmd(cmds.AAE)))
        ui_page2.add(create_ui_text("Disable", 3, 5, size=Size(3, 1), cmd=send_cmd(cmds.AAD)))

        ui_page3 = UiPage("page3", "Configuration", grid=Size(6, 6))
        ui_page3.add(create_ui_text("Clear", 0, 0, size=Size(2, 1), cmd=send_cmd(cmds.CLEAR)))
        ui_page3.add(create_ui_icon("uc:up-arrow", 2, 0, size=Size(2, 1), cmd=send_cmd(cmds.UP)))
        ui_page3.add(create_ui_text("Help", 4, 0, size=Size(2, 0), cmd=send_cmd(cmds.HELP)))
        ui_page3.add(create_ui_icon("uc:left-arrow", 0, 1, size=Size(2, 1), cmd=send_cmd(cmds.LEFT)))
        ui_page3.add(create_ui_icon("uc:circle", 2, 1, size=Size(2, 1), cmd=send_cmd(cmds.OK)))
        ui_page3.add(create_ui_icon("uc:right-arrow", 4, 1, size=Size(2, 1), cmd=send_cmd(cmds.RIGHT)))
        ui_page3.add(create_ui_text("Exit", 0, 2, size=Size(2, 1), cmd=send_cmd(cmds.EXIT)))
        ui_page3.add(create_ui_icon("uc:down-arrow", 2, 2, size=Size(2, 1), cmd=send_cmd(cmds.DOWN)))
        ui_page3.add(create_ui_text("Menu", 4, 2, size=Size(2, 1), cmd=send_cmd(cmds.MENU)))
        ui_page3.add(create_ui_text("HDR Setup", 0, 3, size=Size(6, 1), cmd=send_cmd(cmds.HDR)))
        ui_page3.add(create_ui_text("Pattern", 0, 4, size=Size(6, 1), cmd=send_cmd(cmds.PATTERN)))
        ui_page3.add(create_ui_text("Save", 0, 5, size=Size(6, 1), cmd=send_cmd(cmds.SAVE)))

        ui_page4 = UiPage("page4", "Miscellaneous", grid=Size(4, 4))
        ui_page4.add(create_ui_text("-- OnScreen Messages --", 0, 0, size=Size(4, 1)))
        ui_page4.add(create_ui_text("Enable", 0, 1, size=Size(2, 1), cmd=send_cmd(cmds.MSG_ON)))
        ui_page4.add(create_ui_text("Disable", 2, 1, size=Size(2, 1), cmd=send_cmd(cmds.MSG_OFF)))
        ui_page4.add(create_ui_text("-- Memory Select --", 0, 2, size=Size(4, 1)))
        ui_page4.add(create_ui_text("A", 0, 3, size=Size(1, 1), cmd=send_cmd(cmds.MEMA)))
        ui_page4.add(create_ui_text("B", 1, 3, size=Size(1, 1), cmd=send_cmd(cmds.MEMB)))
        ui_page4.add(create_ui_text("C", 2, 3, size=Size(1, 1), cmd=send_cmd(cmds.MEMC)))
        ui_page4.add(create_ui_text("D", 3, 3, size=Size(1, 1), cmd=send_cmd(cmds.MEMD)))

        return [ui_page1, ui_page2, ui_page3, ui_page4]

    async def command(self, cmd_id: str, params: dict[str, Any] | None = None) -> StatusCodes:
        """
        Handle command requests from the integration API for the remote entity.
        """
        params = params or {}
        if params:
            _LOG.info("Received Remote command request: %s with parameters: %s", cmd_id, params)
        else:
            _LOG.info("Received Remote command request: %s - no parameters", cmd_id)

        status = StatusCodes.BAD_REQUEST  # Default fallback

        try:
            cmd = Commands(cmd_id)
        except ValueError:
            status = StatusCodes.NOT_IMPLEMENTED
        else:
            match cmd:
                case Commands.ON:
                    status = await self._device.power_on()

                case Commands.OFF:
                    status = await self._device.power_off()

                case Commands.TOGGLE:
                    status = await self._device.power_toggle()

                case Commands.SEND_CMD:
                    simple_cmd = params.get("command")

                    if not simple_cmd:
                        _LOG.warning("Missing command in SEND_CMD")
                        status = StatusCodes.BAD_REQUEST
                    elif simple_cmd not in cmds._value2member_map_:
                        _LOG.warning("Unknown command: %s", simple_cmd)
                        status = StatusCodes.NOT_IMPLEMENTED
                    else:
                        try:
                            _LOG.debug("SimpleCommand = %s", simple_cmd)
                            executor_method = getattr(self._device.device.executor, simple_cmd, None)

                            if not callable(executor_method):
                                _LOG.warning("No executor method found for command: %s", simple_cmd)
                                status = StatusCodes.NOT_IMPLEMENTED
                            else:
                                result = executor_method()
                                if asyncio.iscoroutine(result):
                                    await result
                                _LOG.debug("Executed command: %s via executor", simple_cmd)
                                status = StatusCodes.OK
                        except (ValueError, KeyError, AttributeError, TypeError) as e:
                            _LOG.error("Error executing command %s: %s", simple_cmd, e)
                            status = StatusCodes.BAD_REQUEST
                case _:
                    status = StatusCodes.NOT_IMPLEMENTED

        return status


    def filter_changed_attributes(self, update: dict[str, Any]) -> dict[str, Any]:
        """
        Filter the given media-player attributes and return remote attributes with converted state.

        :param update: dictionary with MediaAttributes.
        :return: dictionary with changed remote.Attributes only.
        """
        if MediaAttributes.STATE not in update:
            return {}

        media_state = update[MediaAttributes.STATE]
        new_state = REMOTE_STATE_MAPPING.get(media_state, States.UNKNOWN)

        if Attributes.STATE not in self.attributes or self.attributes[Attributes.STATE] != new_state:
            result = {Attributes.STATE: new_state}
        else:
            result = {}

        _LOG.debug("Remote state changed from %s to %s based on media update %s",
                self.attributes.get(Attributes.STATE), new_state, update)
        return result

def send_cmd(command: cmds):
    """
    Wraps a SimpleCommand enum into a UI-compatible send command payload.

    :param command: A SimpleCommands enum member (e.g. SimpleCommands.UP).
    :return: A dictionary payload compatible with remote.create_send_cmd().
    """
    return remote.create_send_cmd(command.value)
