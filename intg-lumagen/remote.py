"""
Remote entity functions.

:copyright: (c) 2023 by Unfolded Circle ApS.
:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from const import RemoteDef
from const import SimpleCommands as cmds
from device import LumagenDevice, LumagenInfo
from ucapi import Remote, StatusCodes
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
            f"{info.name} Remote",
            features,
            attributes,
            simple_commands=RemoteDef.simple_commands,
            button_mapping=self.create_button_mappings(),
            ui_pages=self.create_ui()
        )

        _LOG.debug("LumagenRemote init %s : %s", entity_id, attributes)


    def create_button_mappings(self) -> list[DeviceButtonMapping | dict[str, Any]]:
        """Create button mappings."""

        button_mappings = [
            create_btn_mapping(Buttons.DPAD_UP, cmds.UP.name),
            create_btn_mapping(Buttons.DPAD_DOWN, cmds.DOWN.name),
            create_btn_mapping(Buttons.DPAD_LEFT, cmds.LEFT.name),
            create_btn_mapping(Buttons.DPAD_RIGHT, cmds.RIGHT.name),
            create_btn_mapping(Buttons.DPAD_MIDDLE, cmds.OK.name),
            create_btn_mapping(Buttons.PREV, cmds.PREV.name),
            create_btn_mapping(Buttons.NEXT, cmds.ALT.name),
            #create_btn_mapping(Buttons.HOME, cmds.MENU.value),
            #create_btn_mapping(Buttons.BACK, cmds.EXIT.value),
            #DeviceButtonMapping(button="MENU", short_press=EntityCommand(cmd_id="menu", params=None), long_press=None)
        ]

        for item in button_mappings:
            _LOG.debug(item)
        return button_mappings

    def create_ui(self) -> list[UiPage | dict[str, Any]]:
        """Create a user interface with different pages that includes all commands"""

        ui_page1 = UiPage("page1", "Power & Input", grid=Size(6, 6))
        ui_page1.add(create_ui_text("Power On", 0, 0, Size(6, 1), Commands.ON))
        ui_page1.add(create_ui_text("1", 0, 1, Size(2, 1), cmds.NUM_1.name))
        ui_page1.add(create_ui_text("2", 2, 1, Size(2, 1), cmds.NUM_2.name))
        ui_page1.add(create_ui_text("3", 4, 1, Size(2, 1), cmds.NUM_3.name))
        ui_page1.add(create_ui_text("4", 0, 2, Size(2, 1), cmds.NUM_4.name))
        ui_page1.add(create_ui_text("5", 2, 2, Size(2, 1), cmds.NUM_5.name))
        ui_page1.add(create_ui_text("6", 4, 2, Size(2, 1), cmds.NUM_6.name))
        ui_page1.add(create_ui_text("7", 0, 3, Size(2, 1), cmds.NUM_7.name))
        ui_page1.add(create_ui_text("8", 2, 3, Size(2, 1), cmds.NUM_8.name))
        ui_page1.add(create_ui_text("9", 4, 3, Size(2, 1), cmds.NUM_9.name))
        ui_page1.add(create_ui_text("10+", 0, 4, Size(2, 1), cmds.NUM_10.name))
        ui_page1.add(create_ui_text("0", 2, 4, Size(2, 1), cmds.NUM_0.name))
        ui_page1.add(create_ui_text("Input", 4, 4, Size(2, 1), cmds.INPUT.name))
        ui_page1.add(create_ui_text("Standby", 0, 5, Size(6, 1), Commands.OFF))

        ui_page2 = UiPage("page2", "Source Aspect Ratios", grid=Size(6, 6))
        ui_page2.add(create_ui_text("4:3", 0, 0, Size(2, 1), cmds.ASPECT_4_X_3.name))
        ui_page2.add(create_ui_text("Lbox", 2, 0, Size(2, 1), cmds.LBOX.name))
        ui_page2.add(create_ui_text("16:9", 4, 0, Size(2, 1), cmds.ASPECT_16_X_9.name))
        ui_page2.add(create_ui_text("1.85", 0, 1, Size(2, 1), cmds.ASPECT_1_85.name))
        ui_page2.add(create_ui_text("1.90", 2, 1, Size(2, 1), cmds.ASPECT_1_90.name))
        ui_page2.add(create_ui_text("2.00", 4, 1, Size(2, 1), cmds.ASPECT_2_00.name))
        ui_page2.add(create_ui_text("2.10", 0, 2, Size(2, 1), cmds.ASPECT_2_10.name))
        ui_page2.add(create_ui_text("2.20", 2, 2, Size(2, 1), cmds.ASPECT_2_20.name))
        ui_page2.add(create_ui_text("2.35", 4, 2, Size(2, 1), cmds.ASPECT_2_35.name))
        ui_page2.add(create_ui_text("2.40", 0, 3, Size(2, 1), cmds.ASPECT_2_40.name))
        ui_page2.add(create_ui_text("2.55", 2, 3, Size(2, 1), cmds.ASPECT_2_55.name))
        ui_page2.add(create_ui_text("NLS", 4, 3, Size(2, 1), cmds.NLS.name))
        ui_page2.add(create_ui_text("-- Auto Aspect --", 0, 4, Size(6, 1)))
        ui_page2.add(create_ui_text("Enable", 0, 5, Size(3, 1), cmds.AAE.name))
        ui_page2.add(create_ui_text("Disable", 3, 5, Size(3, 1), cmds.AAD.name))

        ui_page3 = UiPage("page3", "Configuration", grid=Size(6, 6))
        ui_page3.add(create_ui_text("Clear", 0, 0, Size(2, 1), cmds.CLEAR.name))
        ui_page3.add(create_ui_icon("uc:up-arrow", 2, 0, Size(2, 1), cmds.UP.name))
        ui_page3.add(create_ui_text("Help", 4, 0, Size(2, 1), cmds.HELP.name))
        ui_page3.add(create_ui_icon("uc:left-arrow", 0, 1, Size(2, 1), cmds.LEFT.name))
        ui_page3.add(create_ui_icon("uc:circle", 2, 1, Size(2, 1), cmds.OK.name))
        ui_page3.add(create_ui_icon("uc:right-arrow", 4, 1, Size(2, 1), cmds.RIGHT.name))
        ui_page3.add(create_ui_text("Exit", 0, 2, Size(2, 1), cmds.EXIT.name))
        ui_page3.add(create_ui_icon("uc:down-arrow", 2, 2, Size(2, 1), cmds.DOWN.name))
        ui_page3.add(create_ui_text("Menu", 4, 2, Size(2, 1), cmds.MENU.name))
        ui_page3.add(create_ui_text("HDR Setup", 0, 3, Size(6, 1), cmds.HDR.name))
        ui_page3.add(create_ui_text("Pattern", 0, 4, Size(6, 1), cmds.PATTERN.name))
        ui_page3.add(create_ui_text("Save", 0, 5, Size(6, 1), cmds.SAVE.name))

        ui_page4 = UiPage("page4", "Miscellaneous", grid=Size(4, 4))
        ui_page4.add(create_ui_text("-- OnScreen Messages --", 0, 0, Size(4, 1)))
        ui_page4.add(create_ui_text("Send Test", 0, 1, Size(2, 1), cmds.MSG_ON.name))
        ui_page4.add(create_ui_text("Clear", 2, 1, Size(2, 1), cmds.MSG_OFF.name))
        ui_page4.add(create_ui_text("-- Select Memory Bank --", 0, 2, Size(4, 1)))
        ui_page4.add(create_ui_text("A", 0, 3, Size(1, 1), cmds.MEMA.name))
        ui_page4.add(create_ui_text("B", 1, 3, Size(1, 1), cmds.MEMB.name))
        ui_page4.add(create_ui_text("C", 2, 3, Size(1, 1), cmds.MEMC.name))
        ui_page4.add(create_ui_text("D", 3, 3, Size(1, 1), cmds.MEMD.name))

        return [ui_page1, ui_page2, ui_page3, ui_page4]

    async def command(self, cmd_id: str, params: dict[str, Any] | None = None) -> StatusCodes:
        """
        Handle command requests from the integration API for the remote entity.
        """
        params = params or {}

        simple_cmd: str | None = params.get("command")
        if simple_cmd and simple_cmd.startswith("remote"):
            cmd_id = simple_cmd.split(".")[1]

        _LOG.info("Received Remote command request: %s with parameters: %s", cmd_id, params or "no parameters")


        status = StatusCodes.BAD_REQUEST  # Default fallback

        try:
            cmd = Commands(cmd_id)
            _LOG.debug("Resolved command: %s", cmd)
        except ValueError:
            status = StatusCodes.NOT_IMPLEMENTED
        else:
            match cmd:
                case Commands.ON:
                    status = await self._device.power_on()

                case Commands.OFF:
                    status = await self._device.power_off()

                case Commands.SEND_CMD:
                    if not simple_cmd:
                        _LOG.warning("Missing command in SEND_CMD")
                        status = StatusCodes.BAD_REQUEST
                    else:
                        command_enum = None

                    # First: try direct enum name match (e.g. "LEFT")
                    if simple_cmd in cmds.__members__:
                        command_enum = cmds[simple_cmd]

                    else:
                        # Second: try display_name match (e.g. "1.85", "4x3")
                        for cmd in cmds:
                            if cmd.display_name == simple_cmd:
                                command_enum = cmd
                                break

                    if command_enum:
                        actual_cmd = command_enum.value
                        cmd_params = None

                        if actual_cmd.isdigit() and 0 <= int(actual_cmd) <= 10:
                            actual_cmd = f"send_{actual_cmd}"
                        elif actual_cmd == "display_message":
                            cmd_params = {"timeout": 3, "message": "This is a Test Message from the UC Remote."}
                        elif actual_cmd == "input":
                            try:
                                index = self._device.source_list.index(self._device.source)
                                cmd_params = (index,)
                            except ValueError:
                                _LOG.warning("Current source not in source list")
                                actual_cmd = None
                                status = StatusCodes.BAD_REQUEST

                        if actual_cmd:
                            status = await self._device.send_command(actual_cmd, cmd_params)
                    else:
                        _LOG.warning("Unknown command: %s", simple_cmd)
                        status = StatusCodes.NOT_IMPLEMENTED

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
