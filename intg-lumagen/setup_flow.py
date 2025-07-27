"""
Initial setup and configuration logic for Lumagen integration.

Handles user interaction, automatic discovery of Lumagen devices,
and device onboarding into the system.
"""

import logging

import config
import ucapi
from api import api
from device import LumagenDevice
from discover import ITACH_PORT, discover_itach_devices
from registry import clear_devices

_LOG = logging.getLogger(__name__)


def _basic_input_form(ip: str = "", port: int = ITACH_PORT) -> ucapi.RequestUserInput:
    """
    Returns a form for manual configuration of IP and port.

    Args:
        ip (str): IP address to prepopulate. Default is empty.
        port (int): Port number to prepopulate. Default is ITACH_PORT.

    Returns:
        ucapi.RequestUserInput: Form requesting user input for IP and port.
    """
    return ucapi.RequestUserInput(
        {"en": "Manual Configuration"},
        [
            {"id": "ip", "label": {"en": "Enter IP2SL IP Address:"}, "field": {"text": {"value": ip}}},
            {"id": "port", "label": {"en": "Enter IP2SL Port:"}, "field": {"number": {"value": port}}},
        ]
    )

async def driver_setup_handler(msg: ucapi.SetupDriver) -> ucapi.SetupAction:
    """
    Main entry point for handling all setup-related UCAPI messages.

    Args:
        msg (ucapi.SetupDriver): Message from UCAPI.

    Returns:
        ucapi.SetupAction: Action to take in response to the setup request.
    """

    if isinstance(msg, ucapi.DriverSetupRequest):
        return await handle_driver_setup(msg)
    if isinstance(msg, ucapi.UserDataResponse):
        return await handle_user_data_response(msg)
    if isinstance(msg, ucapi.AbortDriverSetup):
        _LOG.info("Setup was aborted with code: %s", msg.error)
        clear_devices()

    _LOG.error("Error during setup")
    return ucapi.SetupError()

async def handle_driver_setup(msg: ucapi.DriverSetupRequest) -> ucapi.SetupAction:
    """
    Handle initial setup or reconfiguration request from the user.

    Args:
        msg (ucapi.DriverSetupRequest): Setup message containing context and flags.

    Returns:
        ucapi.SetupAction: Action (form, complete, or error) based on discovery result.
    """
    _LOG.info(msg)

    if msg.reconfigure:
        _LOG.info("Starting reconfiguration")

    api.available_entities.clear()
    api.configured_entities.clear()

    if msg.setup_data.get("manual") == "true":
        _LOG.info("Entering manual setup settings")
        return _basic_input_form()

    ip = await discover_itach_devices()
    if not ip:
        return ucapi.SetupError()

    _LOG.info("Using host ip = %s", ip)

    return ucapi.RequestUserInput(
        {"en": "Discovered Lumagen"},
        [
            {
                "id": "ip",
                "label": {"en": "Discovered Lumagen connected to IP2SL IP Address:"},
                "field": {"text": {"value": ip}},
            },
            {
                "id": "port",
                "label": {"en": "IP2SL Port:"},
                "field": {"number": {"value": ITACH_PORT}},
            },
        ]
    )

async def handle_user_data_response(msg: ucapi.UserDataResponse) -> ucapi.SetupAction:
    """
    Handle the user's submitted data from the input form and validate device.

    Args:
        msg (ucapi.UserDataResponse): Contains IP and port info submitted by the user.

    Returns:
        ucapi.SetupAction: Action signaling success or failure of setup.
    """
    _LOG.info(msg)

    config.devices.clear()

    ip = msg.input_values.get("ip")
    port = int(msg.input_values.get("port"))

    controller = LumagenDevice(ip, port, discovery=True)

    if not await controller.connect():
        return ucapi.SetupError()

    try:
        dv_info = await controller.get_info()
        if not dv_info:
            _LOG.error("Unable to retrieve device info from %s", ip)
            return ucapi.SetupError()

        _LOG.debug("Identified device: %s", dv_info)
        config.devices.add(dv_info)

    finally:
        await controller.disconnect()

    _LOG.info("Setup complete")
    return ucapi.SetupComplete()
