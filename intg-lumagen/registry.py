"""
Registry for active LumagenController instances.

Used to store and retrieve controller connections by device ID without causing import cycles.
"""

from typing import Dict, Iterator

from lumagen import LumagenDevice

_configured_lumagens: Dict[str, LumagenDevice] = {}


def get_controller(device_id: str) -> LumagenDevice | None:
    """
    Retrieve the controller associated with a given device ID.

    Args:
        device_id: Unique identifier for the Lumagen device.

    Returns:
        The corresponding LumagenController instance, or None if not found.
    """
    return _configured_lumagens.get(device_id)


def register_controller(device_id: str, controller: LumagenDevice) -> None:
    """
    Register a LumagenController for a given device ID.

    Args:
        device_id: Unique identifier for the Lumagen device.
        controller: Controller instance to associate with the device.
    """
    if device_id not in _configured_lumagens:
        _configured_lumagens[device_id] = controller


def unregister_controller(device_id: str) -> None:
    """
    Remove the controller associated with the given device ID.

    Args:
        device_id: Unique identifier of the device to remove.
    """
    _configured_lumagens.pop(device_id, None)


def all_controllers() -> Dict[str, LumagenDevice]:
    """
    Get a dictionary of all currently registered controllers.

    Returns:
        A dictionary mapping device IDs to their LumagenController instances.
    """
    return _configured_lumagens


def clear_controllers() -> None:
    """
    Remove all registered controllers from the registry.
    """
    _configured_lumagens.clear()


async def connect_all() -> None:
    """
    Connect all registered LumagenController instances asynchronously.
    """
    for controller in iter_controllers():
        await controller.connect()


async def disconnect_all() -> None:
    """
    Disconnect all registered LumagenController instances asynchronously.
    """
    for controller in iter_controllers():
        await controller.disconnect()


def iter_controllers() -> Iterator[LumagenDevice]:
    """
    Yield each registered LumagenController instance.

    Returns:
        An iterator over all registered controller objects.
    """
    return iter(_configured_lumagens.values())
