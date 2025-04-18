#!/usr/bin/env python3
"""Lumagen integration driver."""

import logging
from typing import Any

import config
import ucapi
from api import api, loop
from lumagen import Events, LumagenDevice, LumagenInfo
from media_player import LumagenMediaPlayer
from registry import (clear_controllers, connect_all, disconnect_all,
                      get_controller, register_controller,
                      unregister_controller)
from remote import LumagenRemote
from setup_flow import driver_setup_handler
from utils import map_state_to_remote, setup_logger

_LOG = logging.getLogger("driver")



@api.listens_to(ucapi.Events.CONNECT)
async def on_connect() -> None:
    """Connect all configured receivers when the Remote Two sends the connect command."""
    _LOG.info("Received connect event message from remote")
    await api.set_device_state(ucapi.DeviceStates.CONNECTED)
    loop.create_task(connect_all())


@api.listens_to(ucapi.Events.DISCONNECT)
async def on_r2_disconnect() -> None:
    """Disconnect notification from the Remote Two."""

    _LOG.info("Received disconnect event message from remote")
    await api.set_device_state(ucapi.DeviceStates.DISCONNECTED)
    loop.create_task(disconnect_all())


@api.listens_to(ucapi.Events.ENTER_STANDBY)
async def on_r2_enter_standby() -> None:
    """
    Enter standby notification from Remote Two.

    Disconnect every Lumagen instance.
    """

    _LOG.debug("Enter standby event: disconnecting device(s)")
    loop.create_task(disconnect_all())


@api.listens_to(ucapi.Events.EXIT_STANDBY)
async def on_r2_exit_standby() -> None:
    """
    Exit standby notification from Remote Two.

    Connect all Lumagen instances.
    """

    _LOG.debug("Exit standby event: connecting device(s)")
    loop.create_task(connect_all())


@api.listens_to(ucapi.Events.SUBSCRIBE_ENTITIES)
async def on_subscribe_entities(entity_ids: list[str]) -> None:
    """
    Subscribe to given entities.

    :param entity_ids: entity identifiers.
    """
    _LOG.debug("Subscribe entities event: %s", entity_ids)


@api.listens_to(ucapi.Events.UNSUBSCRIBE_ENTITIES)
async def on_unsubscribe_entities(entity_ids: list[str]) -> None:
    """On unsubscribe, we disconnect the objects and remove listeners for events."""
    _LOG.debug("Unsubscribe entities event: %s", entity_ids)


def _configure_new_lumagen(device: LumagenInfo, connect: bool = True) -> None:
    """
    Create and configure a new Lumagen device.

    If a controller already exists for the given device ID, reuse it.
    Otherwise, create and register a new one.

    :param device: The Lumagen device configuration.
    :param connect: Whether to initiate connection immediately.
    """
    controller = get_controller(device.id)
    if controller is None:
        controller = LumagenDevice(device.address, device.port, device_id=device.id)

        controller.events.on(Events.CONNECTED.name, on_lumagen_connected)
        controller.events.on(Events.DISCONNECTED.name, on_lumagen_disconnected)
        controller.events.on(Events.UPDATE.name, on_lumagen_update)
        #controller.events.on(Events.ERROR, on_avr_connection_error)
        #controller.events.on(Events.IP_ADDRESS_CHANGED, handle_avr_address_change)

        register_controller(device.id, controller)

    if connect:
        loop.create_task(controller.connect())

    _register_available_entities(device, controller)


def _register_available_entities(info: LumagenInfo, controller: LumagenDevice) -> None:
    """
    Register remote and media player entities for a Lumagen device and associate its controller.

    :param info: Lumagen configuration
    :param controller: Active LumagenController for the device
    """
    for entity_cls in (LumagenRemote, LumagenMediaPlayer):
        entity = entity_cls(info, controller)
        if api.available_entities.contains(entity.id):
            api.available_entities.remove(entity.id)
        api.available_entities.add(entity)

    register_controller(info.id, controller)


async def on_lumagen_connected(device_id: str):
    """Handle Lumagen connection."""
    _LOG.debug("Lumagen connected: %s", device_id)

    if not get_controller(device_id):
        _LOG.warning("Lumagen %s is not configured", device_id)
        return

    await api.set_device_state(ucapi.DeviceStates.CONNECTED)

async def on_lumagen_disconnected(device_id: str):
    """Handle Lumagen disconnection."""
    _LOG.debug("Lumagen disconnected: %s", device_id)

    if not get_controller(device_id):
        _LOG.warning("Lumagen %s is not configured", device_id)
        return

    await api.set_device_state(ucapi.DeviceStates.DISCONNECTED)

async def on_lumagen_update(update: dict[str, Any]) -> None:
    """
    Handle state updates emitted by Lumagen and update both media player and remote entities.
    """
    _LOG.debug("handle_lumagen_update: %s", update)

    device_id = update.get("device_id")
    state = update.get("state")

    if device_id is None:
        _LOG.warning("Lumagen update missing 'device_id': %s", update)
        return

    if state is None:
        _LOG.warning("Lumagen update missing 'state': %s", update)
        return

    updates = [
        (f"media_player.{device_id}", ucapi.media_player.Attributes.STATE, state),
        (f"remote.{device_id}", ucapi.remote.Attributes.STATE, map_state_to_remote(state)),
    ]

    for entity_id, attr_key, attr_value in updates:
        if api.configured_entities.contains(entity_id):
            api.configured_entities.update_attributes(entity_id, {attr_key: attr_value})


def on_device_added(device: config.LumagenInfo) -> None:
    """Handle a newly added device in the configuration."""
    _LOG.debug("New device added: %s", device)
    loop.create_task(api.set_device_state(ucapi.DeviceStates.CONNECTED))
    _configure_new_lumagen(device, connect=False)


def on_device_removed(device: config.LumagenInfo | None) -> None:
    """Handle removal of a Lumagen device from config."""
    if device is None:
        _LOG.info("All devices cleared from config.")
        clear_controllers()
        api.configured_entities.clear()
        api.available_entities.clear()
        return

    controller = get_controller(device.id)
    if controller:
        unregister_controller(device.id)
        loop.create_task(_async_remove(controller))
        api.configured_entities.remove(f"media_player.{device.id}")
        api.configured_entities.remove(f"remote.{device.id}")
        _LOG.info("Controller for device %s cleaned up", device.id)
    else:
        _LOG.debug("No controller found for removed device %s", device.id)


async def _async_remove(controller: LumagenDevice) -> None:
    """Disconnect from receiver and remove all listeners."""
    await controller.disconnect()
    controller.events.remove_all_listeners()


async def main():
    """Start the Remote Two integration driver."""

    logging.basicConfig(
        format=(
            "%(asctime)s.%(msecs)03d | %(levelname)-8s | "
            "%(name)-14s | %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    setup_logger()

    _LOG.debug("Starting driver...")
    await api.init("driver.json", driver_setup_handler)

    config.devices = config.Devices(api.config_dir_path, on_device_added, on_device_removed)
    for device in config.devices:
        _configure_new_lumagen(device, connect=False)


if __name__ == "__main__":
    try:
        loop.run_until_complete(main())
        loop.run_forever()
    except KeyboardInterrupt:
        pass
