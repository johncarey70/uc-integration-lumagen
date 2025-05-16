#!/usr/bin/env python3
"""Lumagen Remote Two/3 Integration Driver."""

import logging
from typing import Any

import config
import ucapi
from api import api, loop
from lumagen import Events, LumagenDevice, LumagenInfo
from media_player import LumagenMediaPlayer
from registry import (all_devices, clear_devices, connect_all, disconnect_all,
                      get_device, register_device, unregister_device)
from remote import REMOTE_STATE_MAPPING, LumagenRemote
from setup_flow import driver_setup_handler
from ucapi.media_player import Attributes as MediaAttr
from ucapi.media_player import States
from utils import setup_logger

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

    for entity_id in entity_ids:
        entity = api.configured_entities.get(entity_id)
        if not entity:
            continue

        device_id = config.extract_device_id(entity)
        device = get_device(device_id)

        if device:
            _update_entity_attributes(entity_id, entity, device.attributes)
            continue

        device = config.devices.get(device_id)
        if device:
            _configure_new_lumagen(device, connect=True)
        else:
            _LOG.error("Failed to subscribe entity %s: no Lumagen configuration found", entity_id)


def _update_entity_attributes(entity_id: str, entity, attributes: dict):
    """
    Update attributes for the given entity based on its type.
    """
    if isinstance(entity, LumagenMediaPlayer):
        api.configured_entities.update_attributes(entity_id, attributes)
    elif isinstance(entity, LumagenRemote):
        api.configured_entities.update_attributes(
            entity_id,
            {
                ucapi.remote.Attributes.STATE:
                REMOTE_STATE_MAPPING.get(attributes.get(MediaAttr.STATE, States.UNKNOWN))
            }
        )


@api.listens_to(ucapi.Events.UNSUBSCRIBE_ENTITIES)
async def on_unsubscribe_entities(entity_ids: list[str]) -> None:
    """On unsubscribe, disconnect devices only if no other entities are using them."""
    _LOG.debug("Unsubscribe entities event: %s", entity_ids)

    # Collect devices associated with the entities being unsubscribed
    devices_to_remove = {
        config.extract_device_id(api.configured_entities.get(entity_id))
        for entity_id in entity_ids
        if api.configured_entities.get(entity_id)
    }

    # Check other remaining entities to see if they still use these devices
    remaining_entities = [
        e for e in api.configured_entities.get_all()
        if e.get("entity_id") not in entity_ids
    ]

    for entity in remaining_entities:
        device_id = config.extract_device_id(entity)
        devices_to_remove.discard(device_id)  # discard safely removes if present

    # Disconnect and clean up devices no longer in use
    for device_id in devices_to_remove:
        if device_id in all_devices():
            device = get_device(device_id)
            await device.disconnect()
            device.events.remove_all_listeners()



def _configure_new_lumagen(info: LumagenInfo, connect: bool = False) -> None:
    """
    Create and configure a new Lumagen device.

    If a device already exists for the given device ID, reuse it.
    Otherwise, create and register a new one.

    :param info: The Lumagen device configuration.
    :param connect: Whether to initiate connection immediately.
    """
    device = get_device(info.id)
    if device:
        device.disconnect()
    else:
        device = LumagenDevice(info.address, info.port, device_id=info.id)

        device.events.on(Events.CONNECTED.name, on_lumagen_connected)
        device.events.on(Events.DISCONNECTED.name, on_lumagen_disconnected)
        device.events.on(Events.UPDATE.name, on_lumagen_update)

        register_device(info.id, device)

    if connect:
        loop.create_task(device.connect())

    _register_available_entities(info, device)


def _register_available_entities(info: LumagenInfo, device: LumagenDevice) -> None:
    """
    Register remote and media player entities for a Lumagen device and associate its device.

    :param info: Lumagen configuration
    :param device: Active LumagenDevice for the device
    """
    for entity_cls in (LumagenRemote, LumagenMediaPlayer):
        entity = entity_cls(info, device)
        if api.available_entities.contains(entity.id):
            api.available_entities.remove(entity.id)
        api.available_entities.add(entity)


async def on_lumagen_connected(device_id: str):
    """Handle Lumagen connection."""
    _LOG.debug("Lumagen connected: %s", device_id)

    if not get_device(device_id):
        _LOG.warning("Lumagen %s is not configured", device_id)
        return

    await api.set_device_state(ucapi.DeviceStates.CONNECTED)


async def on_lumagen_disconnected(device_id: str):
    """Handle Lumagen disconnection."""
    _LOG.debug("Lumagen disconnected: %s", device_id)

    if not get_device(device_id):
        _LOG.warning("Lumagen %s is not configured", device_id)
        return

    await api.set_device_state(ucapi.DeviceStates.DISCONNECTED)


async def on_lumagen_update(device_id: str, update: dict[str, Any] | None) -> None:
    """
    Update attributes of configured media-player or remote entity if device attributes changed.

    :param device_id: Device identifier.
    :param update: Dictionary containing the updated attributes or None.
    """
    if update is None:
        return

    device = get_device(device_id)
    if device is None:
        return

    _LOG.debug("[%s] Lumagen update: %s", device_id, update)

    for suffix, cls in [("media_player", LumagenMediaPlayer), ("remote", LumagenRemote)]:
        entity_id = f"{suffix}.{device_id}"
        entity: LumagenMediaPlayer | LumagenRemote | None = api.configured_entities.get(entity_id)

        if not isinstance(entity, cls):
            continue

        changed_attrs = entity.filter_changed_attributes(update)
        if changed_attrs:
            api.configured_entities.update_attributes(entity_id, changed_attrs)


def on_device_added(device: LumagenInfo) -> None:
    """Handle a newly added device in the configuration."""
    _LOG.debug("New Lumagen device added: %s", device)
    loop.create_task(api.set_device_state(ucapi.DeviceStates.CONNECTED))
    _configure_new_lumagen(device, connect=False)


def on_device_removed(device: LumagenInfo | None) -> None:
    """Handle removal of a Lumagen device from config."""
    if device is None:
        _LOG.info("All devices cleared from config.")
        clear_devices()
        api.configured_entities.clear()
        api.available_entities.clear()
        return

    device = get_device(device.id)
    if device:
        unregister_device(device.id)
        loop.create_task(_async_remove(device))
        api.configured_entities.remove(f"media_player.{device.id}")
        api.configured_entities.remove(f"remote.{device.id}")
        _LOG.info("Device for device_id %s cleaned up", device.id)
    else:
        _LOG.debug("No Device found for removed device %s", device.id)


async def _async_remove(device: LumagenDevice) -> None:
    """Disconnect from receiver and remove all listeners."""
    _LOG.debug("Disconnecting and removing all listeners")
    await device.disconnect()
    device.events.remove_all_listeners()


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
