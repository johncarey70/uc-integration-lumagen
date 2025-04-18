"""
Remote entity functions.

:copyright: (c) 2023 by Unfolded Circle ApS.
:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from const import RemoteDef
from const import SimpleCommands as cmd
from lumagen import LumagenDevice, LumagenInfo
from ucapi import Remote, StatusCodes, remote
from ucapi.remote import Commands
from ucapi.ui import (Buttons, DeviceButtonMapping, Size, UiPage,
                      create_btn_mapping, create_ui_icon, create_ui_text)

_LOG = logging.getLogger(__name__)

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
            info.name,
            features,
            attributes,
            simple_commands=RemoteDef.simple_commands,
            button_mapping=self.create_button_mappings(),
            ui_pages=self.create_ui()
        )

    def create_button_mappings(self) -> list[DeviceButtonMapping | dict[str, Any]]:
        """Create button mappings."""
        return [
            create_btn_mapping(Buttons.DPAD_UP, cmd.UP.name),
            create_btn_mapping(Buttons.DPAD_DOWN, cmd.DOWN.name),
            create_btn_mapping(Buttons.DPAD_LEFT, cmd.LEFT.name),
            create_btn_mapping(Buttons.DPAD_RIGHT, cmd.RIGHT.name),
            create_btn_mapping(Buttons.DPAD_MIDDLE, cmd.OK.name),
            create_btn_mapping(Buttons.PREV, cmd.PREV.name),
            create_btn_mapping(Buttons.NEXT, cmd.ALT.name),

            {"button": "POWER", "short_press": {"cmd_id": "remote.toggle"}},
            {"button": "MENU", "short_press": {"cmd_id": cmd.MENU.name}},
        ]

    def create_ui(self) -> list[UiPage | dict[str, Any]]:
        """Create a user interface with different pages that includes all commands"""

        ui_page1 = UiPage("page1", "Power & Input", grid=Size(6, 6))
        ui_page1.add(create_ui_text("Power On", 2, 0, size=Size(6, 1), cmd=Commands.ON))
        ui_page1.add(create_ui_text("1", 0, 1, size=Size(2, 1), cmd=remote.create_send_cmd(cmd.NUM_1.name)))
        ui_page1.add(create_ui_text("2", 2, 1, size=Size(2, 1), cmd=remote.create_send_cmd(cmd.NUM_2.name)))
        ui_page1.add(create_ui_text("3", 4, 1, size=Size(2, 1), cmd=remote.create_send_cmd(cmd.NUM_3.name)))
        ui_page1.add(create_ui_text("4", 0, 2, size=Size(2, 1), cmd=remote.create_send_cmd(cmd.NUM_4.name)))
        ui_page1.add(create_ui_text("5", 2, 2, size=Size(2, 1), cmd=remote.create_send_cmd(cmd.NUM_5.name)))
        ui_page1.add(create_ui_text("6", 4, 2, size=Size(2, 1), cmd=remote.create_send_cmd(cmd.NUM_6.name)))
        ui_page1.add(create_ui_text("7", 0, 3, size=Size(2, 1), cmd=remote.create_send_cmd(cmd.NUM_7.name)))
        ui_page1.add(create_ui_text("8", 2, 3, size=Size(2, 1), cmd=remote.create_send_cmd(cmd.NUM_8.name)))
        ui_page1.add(create_ui_text("9", 4, 3, size=Size(2, 1), cmd=remote.create_send_cmd(cmd.NUM_9.name)))
        ui_page1.add(create_ui_text("10+", 0, 4, size=Size(2, 1), cmd=remote.create_send_cmd(cmd.NUM_10.name)))
        ui_page1.add(create_ui_text("0", 2, 4, size=Size(2, 1), cmd=remote.create_send_cmd(cmd.NUM_0.name)))
        ui_page1.add(create_ui_text("Input", 4, 4, size=Size(2, 1), cmd=remote.create_send_cmd(cmd.INPUT.name)))
        ui_page1.add(create_ui_text("Standby", 0, 5, size=Size(6, 1), cmd=Commands.OFF))

        ui_page2 = UiPage("page2", "Source Aspect Ratios", grid=Size(6, 6))
        ui_page2.add(create_ui_text("4:3", 0, 0, size=Size(2, 1), cmd=remote.create_send_cmd(cmd.A4_3.name)))
        ui_page2.add(create_ui_text("Lbox", 2, 0, size=Size(2, 1), cmd=remote.create_send_cmd(cmd.LBOX.name)))
        ui_page2.add(create_ui_text("16:9", 4, 0, size=Size(2, 1), cmd=remote.create_send_cmd(cmd.A16_9.name)))
        ui_page2.add(create_ui_text("1.85", 0, 1, size=Size(2, 1), cmd=remote.create_send_cmd(cmd.A1_85.name)))
        ui_page2.add(create_ui_text("1.90", 2, 1, size=Size(2, 1), cmd=remote.create_send_cmd(cmd.A1_90.name)))
        ui_page2.add(create_ui_text("2.00", 4, 1, size=Size(2, 1), cmd=remote.create_send_cmd(cmd.A2_00.name)))
        ui_page2.add(create_ui_text("2.10", 0, 2, size=Size(2, 1), cmd=remote.create_send_cmd(cmd.A2_10.name)))
        ui_page2.add(create_ui_text("2.20", 2, 2, size=Size(2, 1), cmd=remote.create_send_cmd(cmd.A2_20.name)))
        ui_page2.add(create_ui_text("2.35", 4, 2, size=Size(2, 1), cmd=remote.create_send_cmd(cmd.A2_35.name)))
        ui_page2.add(create_ui_text("2.40", 0, 3, size=Size(2, 1), cmd=remote.create_send_cmd(cmd.A2_40.name)))
        ui_page2.add(create_ui_text("2.55", 2, 3, size=Size(2, 1), cmd=remote.create_send_cmd(cmd.A2_55.name)))
        ui_page2.add(create_ui_text("NLS", 4, 3, size=Size(2, 1), cmd=remote.create_send_cmd(cmd.NLS.name)))
        ui_page2.add(create_ui_text("-- Auto Aspect --", 0, 4, size=Size(6, 1)))
        ui_page2.add(create_ui_text("Enable", 0, 5, size=Size(3, 1), cmd=remote.create_send_cmd(cmd.AAE.name)))
        ui_page2.add(create_ui_text("Disable", 3, 5, size=Size(3, 1), cmd=remote.create_send_cmd(cmd.AAD.name)))

        ui_page3 = UiPage("page3", "Configuration", grid=Size(6, 6))
        ui_page3.add(create_ui_text("Clear", 0, 0, size=Size(2, 1), cmd=remote.create_send_cmd(cmd.CLEAR.name)))
        ui_page3.add(create_ui_icon("uc:up-arrow", 2, 0, size=Size(2, 1), cmd=remote.create_send_cmd(cmd.UP.name)))
        ui_page3.add(create_ui_text("Help", 4, 0, size=Size(2, 0), cmd=remote.create_send_cmd(cmd.HELP.name)))
        ui_page3.add(create_ui_icon("uc:left-arrow", 0, 1, size=Size(2, 1), cmd=remote.create_send_cmd(cmd.LEFT.name)))
        ui_page3.add(create_ui_icon("uc:circle", 2, 1, size=Size(2, 1), cmd=remote.create_send_cmd(cmd.OK.name)))
        ui_page3.add(create_ui_icon("uc:right-arrow", 4, 1, size=Size(2, 1), cmd=remote.create_send_cmd(cmd.RIGHT.name)))
        ui_page3.add(create_ui_text("Exit", 0, 2, size=Size(2, 1), cmd=remote.create_send_cmd(cmd.EXIT.name)))
        ui_page3.add(create_ui_icon("uc:down-arrow", 2, 2, size=Size(2, 1), cmd=remote.create_send_cmd(cmd.DOWN.name)))
        ui_page3.add(create_ui_text("Menu", 4, 2, size=Size(2, 1), cmd=remote.create_send_cmd(cmd.MENU.name)))
        ui_page3.add(create_ui_text("HDR Setup", 0, 3, size=Size(6, 1), cmd=remote.create_send_cmd(cmd.HDR.name)))
        ui_page3.add(create_ui_text("Pattern", 0, 4, size=Size(6, 1), cmd=remote.create_send_cmd(cmd.PATTERN.name)))
        ui_page3.add(create_ui_text("Save", 0, 5, size=Size(6, 1), cmd=remote.create_send_cmd(cmd.SAVE.name)))

        ui_page4 = UiPage("page4", "Miscellaneous", grid=Size(4, 4))
        ui_page4.add(create_ui_text("-- OnScreen Messages --", 0, 0, size=Size(4, 1)))
        ui_page4.add(create_ui_text("Enable", 0, 1, size=Size(2, 1), cmd=remote.create_send_cmd(cmd.MSG_ON.name)))
        ui_page4.add(create_ui_text("Disable", 2, 1, size=Size(2, 1), cmd=remote.create_send_cmd(cmd.MSG_OFF.name)))
        ui_page4.add(create_ui_text("-- Memory Select --", 0, 2, size=Size(4, 1)))
        ui_page4.add(create_ui_text("A", 0, 3, size=Size(1, 1), cmd=remote.create_send_cmd(cmd.MEMA.name)))
        ui_page4.add(create_ui_text("B", 1, 3, size=Size(1, 1), cmd=remote.create_send_cmd(cmd.MEMB.name)))
        ui_page4.add(create_ui_text("C", 2, 3, size=Size(1, 1), cmd=remote.create_send_cmd(cmd.MEMC.name)))
        ui_page4.add(create_ui_text("D", 3, 3, size=Size(1, 1), cmd=remote.create_send_cmd(cmd.MEMD.name)))

        return [ui_page1, ui_page2, ui_page3, ui_page4]

    async def command(self, cmd_id: str, params: dict[str, Any] | None = None) -> StatusCodes:
        """
        Handle command requests from the integration API for the media-player entity.

        :param cmd_id: Command identifier (e.g., "ON", "OFF", "TOGGLE", "SEND_CMD")
        :param params: Optional dictionary of parameters associated with the command
        :return: Status code indicating the result of the command execution
        """
        if params is None:
            _LOG.info("Received command request: %s - no parameters", cmd_id)
            params = {}
        else:
            _LOG.info("Received command request: %s with parameters: %s", cmd_id, params)

        match cmd_id:
            case remote.Commands.ON:
                await self._device.power_on()

            case remote.Commands.OFF:
                await self._device.power_off()

            case remote.Commands.TOGGLE:
                await self._device.power_toggle()

            case remote.Commands.SEND_CMD:
                raw = params.get("command")
                try:
                    simple_cmd: cmd = raw if isinstance(raw, cmd) else cmd(raw)
                    _LOG.debug("Sending ASCII command: %s", simple_cmd.ascii)
                    await self._device.send(simple_cmd.ascii)
                except ValueError:
                    _LOG.warning("Invalid or unknown command: %s", raw)
                    return StatusCodes.NOT_FOUND

            case _:
                _LOG.info("Unhandled command ID: %s", cmd_id)
                return StatusCodes.BAD_REQUEST

        return StatusCodes.OK
