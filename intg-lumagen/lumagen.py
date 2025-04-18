"""Provides connection utilities for communicating with a Lumagen device."""

import asyncio
import logging
from asyncio import AbstractEventLoop
from dataclasses import dataclass
from enum import Enum, IntEnum

import ucapi
from const import SimpleCommands as cmd
from pyee.asyncio import AsyncIOEventEmitter
from pylumagen.lumagen import DeviceManager
from pylumagen.models.constants import ConnectionStatus, EventType
from ucapi import StatusCodes

_LOG = logging.getLogger(__name__)

class Events(IntEnum):
    """Internal driver events."""

    CONNECTING = 0
    CONNECTED = 1
    DISCONNECTED = 2
    PAIRED = 3
    ERROR = 4
    UPDATE = 5
    IP_ADDRESS_CHANGED = 6

class PowerStateEnum(str, Enum):
    """Power States."""
    UNKNOWN = "unknown"
    ACTIVE = "Active"
    STANDBY = "Standby"

@dataclass
class LumagenInfo:
    """Represents Lumagen Info including identity, network, and metadata information."""
    id: str
    name: str
    address: str
    port: int
    model_name: str | None = None
    software_version: str | None = None
    model_number: str | None = None

    def __repr__(self) -> str:
        return (
            f"<LumagenDevice id='{self.id}' name='{self.name}' "
            f"address='{self.address}:{self.port}' "
            f"model='{self.model_name}' version='{self.software_version}'>"
        )

class LumagenDevice:
    """Handles communication with a Lumagen video processor over TCP."""

    def __init__(self,
                 host: str,
                 port: int,
                 device_id: str | None = None,
                 discovery: bool = False,
                 loop: AbstractEventLoop | None = None
            ):
        self.device_id = device_id  or "unknown"
        self.host = host
        self.port = port
        self.discovery = discovery
        self.current_status: PowerStateEnum = PowerStateEnum.UNKNOWN
        self._event_loop = loop or asyncio.get_running_loop()
        self._connected: bool = False
        self._disconnecting: bool = False
        self._is_alive: bool = False
        self.events = AsyncIOEventEmitter(self._event_loop)
        self.device = DeviceManager(connection_type="ip")
        self.dispatcher = self.device.dispatcher
        self._subscribe_device_state_events()

    def __repr__(self):
        return f"<LumagenDevice id='{self.device_id}' at {self.host}:{self.port}>"

    def _subscribe_device_state_events(self):
        """Subscribe to device state updates from the dispatcher."""

        async def _handle_state_change(attr_name, _, event_data):
            value = event_data.get("value")
            _LOG.debug("State changed: %s -> %s", attr_name, value)
            self.events.emit(attr_name, self.device_id, value)

            if attr_name == "device_status":
                try:
                    self.current_status = PowerStateEnum(value)
                except ValueError:
                    _LOG.warning("Unknown power state received: %s", value)
                    self.current_status = PowerStateEnum.UNKNOWN
            elif attr_name == "is_alive":
                self._is_alive = True

        for attr in ["device_status", "is_alive"]:
            self.dispatcher.register_listener(
                attr,
                lambda et, ed, attr=attr: asyncio.create_task(_handle_state_change(attr, et, ed))
            )

        def handle_connection_state(_, event_data):
            state = event_data.get("state")

            if state == ConnectionStatus.DISCONNECTED:
                _LOG.debug("Connection state: DISCONNECTED")
                self._connected = False
                self._is_alive = False
                self.events.emit(Events.DISCONNECTED.name, self.device_id)

            elif state == ConnectionStatus.CONNECTED:
                label = "IP2SL device" if self.discovery else "Lumagen"
                _LOG.info("Connected to %s at %s:%d", label, self.host, self.port)
                self._connected = True
                self.events.emit(Events.CONNECTED.name, self.device_id)

        self.dispatcher.register_listener(EventType.CONNECTION_STATE, handle_connection_state)

    @property
    def is_powered_on(self) -> bool:
        """Convenience property for checking if device is active."""
        return self.current_status == PowerStateEnum.ACTIVE

    @property
    def is_connected(self) -> bool:
        """Indicates whether the device is currently connected."""
        return self._connected

    @property
    def is_alive(self) -> bool:
        """Indicates whether the device is currently alive."""
        return self._is_alive

    async def connect(self) -> bool:
        """Establish a connection to the device."""
        self.events.emit(Events.CONNECTING.name, self.device_id)
        if self._connected:
            _LOG.debug("Already connected to Lumagen at %s:%d", self.host, self.port)
            return True

        try:
            await self.device.open(host=self.host, port=self.port)
            self._disconnecting = False
            await asyncio.sleep(1)
            return True
        except (OSError, ConnectionError) as e:
            _LOG.error("Failed to connect to Lumagen at %s:%d - %s", self.host, self.port, e)
            return False

    async def disconnect(self):
        """Close the connection cleanly, if not already disconnecting."""
        if self._disconnecting:
            return

        self._disconnecting = True
        _LOG.info("Disconnecting from Lumagen at %s:%d", self.host, self.port)
        await self.device.close()


    async def send(self, data: str) -> str | None:
        """Send data to the Lumagen device."""
        if not self._connected:
            _LOG.error("Connection not established.")
            return None

        await self.device.send_command(data)
        _LOG.debug("Sent: %s", data)

        return StatusCodes.OK

    async def power_on(self) -> ucapi.StatusCodes:
        """Power on the Lumagen device if it is in standby mode."""
        if self.current_status == PowerStateEnum.STANDBY:
            await self.device.send_command(cmd.ON.ascii)
        else:
            _LOG.debug("Power on skipped: Device is already %s.", self.current_status.value)
        return ucapi.StatusCodes.OK

    async def power_off(self) -> ucapi.StatusCodes:
        """Power off the Lumagen device if it is currently active."""
        if self.is_powered_on:
            await self.device.send_command(cmd.STBY.ascii)
        else:
            _LOG.debug("Power off skipped: Device is already %s.", self.current_status.value)
        return ucapi.StatusCodes.OK

    async def power_toggle(self) -> ucapi.StatusCodes:
        """Toggle the power state of the Lumagen device."""
        command = (
            cmd.STBY.ascii
            if self.is_powered_on
            else cmd.ON.ascii
        )
        await self.device.send_command(command)
        return ucapi.StatusCodes.OK

    async def wait_until_connected(self, timeout: float = 10.0) -> bool:
        """Wait until the device emits a CONNECTED event or times out."""
        try:
            await asyncio.wait_for(self.events.once(Events.CONNECTED.name), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False

    async def get_info(self) -> LumagenInfo | None:
        """
        Send an ID query and return parsed device information as a LumagenDevice dataclass.
        Response format: 'RadiancePro,090524,1018,009022'
        """
        response = await self.device.get_device_info()
        if not response:
            _LOG.error("No response received from device info query.")
            return None

        return LumagenInfo(
            id=f"{response.model_number}{response.serial_number}",
            name=response.model_name,
            address=self.host,
            port=self.port,
            model_name=response.model_name,
            software_version=response.software_revision,
            model_number=response.model_number,
        )
