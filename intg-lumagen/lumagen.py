"""Provides connection utilities for communicating with a Lumagen device."""

import asyncio
import logging
from asyncio import AbstractEventLoop
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Any

import ucapi
from const import SimpleCommands
from pyee.asyncio import AsyncIOEventEmitter
from pylumagen.lumagen import DeviceManager
from pylumagen.models.constants import ConnectionStatus, EventType
from ucapi import StatusCodes
from ucapi.media_player import Attributes as MediaAttr
from ucapi.media_player import States
from utils import validate_simple_commands_exist_on_executor

_LOG = logging.getLogger(__name__)

class Events(IntEnum):
    """Internal driver events."""

    CONNECTING = 0
    CONNECTED = 1
    DISCONNECTED = 2
    ERROR = 3
    UPDATE = 4
    IP_ADDRESS_CHANGED = 5

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

    def __init__(
        self,
        host: str,
        port: int,
        device_id: str | None = None,
        discovery: bool = False,
        loop: AbstractEventLoop | None = None,
    ):
        # Identity and connection config
        self.device_id = device_id or "unknown"
        self.host = host
        self.port = port
        self.discovery = discovery

        # Event loop and internal connection state
        self._event_loop = loop or asyncio.get_running_loop()
        self._connected: bool = False
        self._disconnecting: bool = False
        self._is_alive: bool = False
        self._attr_state = States.OFF
        self.current_status: PowerStateEnum = PowerStateEnum.UNKNOWN

        # Device management and communication
        self.device = DeviceManager(connection_type="ip")
        self._source_list = self.device.source_list
        self._active_source = None
        self.dispatcher = self.device.dispatcher
        self.events = AsyncIOEventEmitter(self._event_loop)

        # Internal event subscriptions
        self._subscribe_device_state_events()

    def __repr__(self):
        return f"<LumagenDevice id='{self.device_id}' at {self.host}:{self.port}>"

    def _subscribe_device_state_events(self):
        """Subscribe to device state updates from the dispatcher."""

        attr_handlers = {
            "device_status": self._handle_device_status,
            "is_alive": self._handle_is_alive,
            "input_labels": self._handle_input_labels,
            "physical_input_selected": self._handle_physical_input_selected,
        }

        async def _handle_state_change(attr_name: str, _, event_data: dict):
            value = event_data.get("value")
            _LOG.debug("State changed: %s -> %s", attr_name, value)

            handler = attr_handlers.get(attr_name)
            if handler:
                await handler(value)

        for attr_name in attr_handlers:
            self.dispatcher.register_listener(
                attr_name,
                lambda et, ed, attr=attr_name: asyncio.create_task(_handle_state_change(attr, et, ed))
            )

        self.dispatcher.register_listener(
            EventType.CONNECTION_STATE, self._handle_connection_state
        )

    async def _handle_device_status(self, value: Any) -> None:
        try:
            self.current_status = PowerStateEnum(value)
            if self.current_status == PowerStateEnum.ACTIVE:
                self._attr_state = States.ON
            elif self.current_status == PowerStateEnum.STANDBY:
                self._attr_state = States.STANDBY
            else:
                self._attr_state = States.UNKNOWN
            self.events.emit(Events.UPDATE.name, self.device_id, {MediaAttr.STATE: value})
        except ValueError:
            _LOG.warning("Unknown power state received: %s", value)
            self.current_status = PowerStateEnum.UNKNOWN
            self._attr_state = States.UNKNOWN

    async def _handle_is_alive(self, _: Any) -> None:
        self._is_alive = True

    async def _handle_input_labels(self, value: Any) -> None:
        self.events.emit(Events.UPDATE.name, self.device_id, {MediaAttr.SOURCE_LIST: value})
        self._source_list = self.device.source_list
        _LOG.debug(self.source_list)

    async def _handle_physical_input_selected(self, value: Any) -> None:
        try:
            index = int(value) - 1
            source_name = self._source_list[index] if 0 <= index < len(self._source_list) else None
            if source_name:
                self._active_source = source_name
                self.events.emit(Events.UPDATE.name, self.device_id, {MediaAttr.SOURCE: source_name})
            else:
                _LOG.warning("Invalid physical_input_selected index: %s", value)
        except (ValueError, TypeError):
            _LOG.warning("Unable to process physical_input_selected value: %s", value)

    def _handle_connection_state(self, _, event_data: dict) -> None:
        state = event_data.get("state")

        if state == ConnectionStatus.DISCONNECTED:
            _LOG.debug("Connection state: DISCONNECTED")
            self._connected = False
            self._is_alive = False
            self._attr_state = States.UNAVAILABLE
            self.events.emit(Events.DISCONNECTED.name, self.device_id)

        elif state == ConnectionStatus.CONNECTED:
            label = "IP2SL device" if self.discovery else "Lumagen"
            _LOG.info("Connected to %s at %s:%d", label, self.host, self.port)
            self._connected = True
            self.events.emit(Events.CONNECTED.name, self.device_id)

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

    @property
    def source_list(self) -> list[str]:
        """Return a list of available input sources."""
        return self._source_list

    @property
    def source(self) -> str:
        """Return the current input source."""
        return self._active_source

    @property
    def state(self) -> States:
        """Return the cached state of the device."""
        return self._attr_state

    @property
    def attributes(self) -> dict[str, any]:
        """Return the device attributes."""
        updated_data = {
            MediaAttr.STATE: self.state,
        }
        if self.source_list:
            updated_data[MediaAttr.SOURCE_LIST] = self.source_list
        if self.source:
            updated_data[MediaAttr.SOURCE] = self.source
        return updated_data

    async def connect(self) -> bool:
        """Establish a connection to the device."""

        if self._connected:
            _LOG.debug("Already connected to Lumagen at %s:%d", self.host, self.port)
            return True

        self.events.emit(Events.CONNECTING.name, self.device_id)

        try:
            await self.device.open(host=self.host, port=self.port)
            self._disconnecting = False
            await asyncio.sleep(1)

            if not self.discovery:
                validate_simple_commands_exist_on_executor(SimpleCommands, self.device.executor, _LOG)

                _LOG.debug("Fetching labels after connection...")
                await self.device.executor.get_labels(get_all=False)

            return True
        except (OSError, ConnectionError) as e:
            _LOG.error("Failed to connect to Lumagen at %s:%d - %s", self.host, self.port, e)
            return False

    async def disconnect(self):
        """Close the connection cleanly, if not already disconnecting."""
        if self._disconnecting:
            return

        self._disconnecting = True
        label = "IP2SL device" if self.discovery else "Lumagen"
        _LOG.info("Disconnecting from %s at %s:%d",label, self.host, self.port)
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
            await self.device.executor.power_on()
        else:
            _LOG.debug("Power on skipped: Device is already %s.", self.current_status.value)
        return ucapi.StatusCodes.OK

    async def power_off(self) -> ucapi.StatusCodes:
        """Power off the Lumagen device if it is currently active."""
        if self.is_powered_on:
            await self.device.executor.standby()
        else:
            _LOG.debug("Power off skipped: Device is already %s.", self.current_status.value)
        return ucapi.StatusCodes.OK

    async def power_toggle(self) -> ucapi.StatusCodes:
        """Toggle the power state of the Lumagen device."""
        if self.is_powered_on:
            await self.device.executor.standby()
        else:
            await self.device.executor.power_on()
        return ucapi.StatusCodes.OK

    async def select_source(self, source: str) -> ucapi.StatusCodes:
        """
        Select a video input source on the Lumagen device.

        :param source: Source input as a string, e.g., "HDMI1".
        :return: Status code
        """

        if not source:
            return ucapi.StatusCodes.BAD_REQUEST
        _LOG.debug("Set input: %s", source)

        num = 0
        await self.device.executor.input(num)
        _LOG.info("Sent source select command for input %02d", num)
        return ucapi.StatusCodes.OK

    async def get_info(self) -> LumagenInfo | None:
        """
        Send an ID query and return parsed device information as a LumagenDevice dataclass.
        Response format: 'RadiancePro,090524,1018,001234'
        """
        response = await self.device.get_device_info()
        if not response:
            _LOG.error("No response received from device info query.")
            return None

        return LumagenInfo(
            id=f"{response.model_number}{response.serial_number:06d}",
            name=response.model_name,
            address=self.host,
            port=self.port,
            model_name=response.model_name,
            software_version=response.software_revision,
            model_number=response.model_number,
        )
