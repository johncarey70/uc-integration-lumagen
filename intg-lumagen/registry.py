"""
Registry for active LumagenDevice instances.

Used to store and retrieve device connections by device ID.
"""

from typing import Dict, Iterator

from device import LumagenDevice

_configured_lumagens: Dict[str, LumagenDevice] = {}


def get_device(device_id: str) -> LumagenDevice | None:
    """
    Retrieve the device associated with a given device ID.

    Args:
        device_id: Unique identifier for the Lumagen device.

    Returns:
        The corresponding LumagenDevice instance, or None if not found.
    """
    return _configured_lumagens.get(device_id)


def register_device(device_id: str, device: LumagenDevice) -> None:
    """
    Register a LumagenDevice for a given device ID.

    Args:
        device_id: Unique identifier for the Lumagen device.
        device: LumagenDevice instance to associate with the device.
    """

    if device_id not in _configured_lumagens:
        _configured_lumagens[device_id] = device


def unregister_device(device_id: str) -> None:
    """
    Remove the device associated with the given device ID.

    Args:
        device_id: Unique identifier of the device to remove.
    """
    _configured_lumagens.pop(device_id, None)


def all_devices() -> Dict[str, LumagenDevice]:
    """
    Get a dictionary of all currently registered devices.

    Returns:
        A dictionary mapping device IDs to their LumagenDevice instances.
    """
    return _configured_lumagens


def clear_devices() -> None:
    """
    Remove all registered devicess from the registry.
    """
    _configured_lumagens.clear()


async def connect_all() -> None:
    """
    Connect all registered LumagenDevice instances asynchronously.
    """
    for device in iter_devices():
        await device.connect()


async def disconnect_all() -> None:
    """
    Disconnect all registered LumagenDevice instances asynchronously.
    """
    for device in iter_devices():
        await device.disconnect()


def iter_devices() -> Iterator[LumagenDevice]:
    """
    Yield each registered LumagenDevice instance.

    Returns:
        An iterator over all registered device objects.
    """
    return iter(_configured_lumagens.values())
