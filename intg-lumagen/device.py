"""Provides connection utilities for communicating with a Lumagen device."""

import asyncio
import inspect
import logging
from asyncio import AbstractEventLoop
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Any

import ucapi
from const import EntityPrefix
from pyee.asyncio import AsyncIOEventEmitter
from pylumagen.lumagen import DeviceInfo, DeviceManager, CommandExecutor
from pylumagen.models.constants import ConnectionStatus, EventType
from ucapi import StatusCodes
from ucapi.media_player import Attributes as MediaAttr
from ucapi.media_player import States
from ucapi.sensor import Attributes as SensorAttr

ParamType = str | int | float | bool
ParamTuple = tuple[ParamType, ...]
ParamDict = dict[str, ParamType]

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
    """Dataclass for device identity and metadata."""
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
        self.device = DeviceManager(connection_type="ip", reconnect=False)
        self._source_list = self.device.source_list
        self._active_source = None
        self.dispatcher = self.device.dispatcher
        self.events = AsyncIOEventEmitter(self._event_loop)

        # Internal event subscriptions
        self._attr_handlers = {
            "device_status": self._handle_device_status,
            "is_alive": self._handle_is_alive,
            "input_labels": self._handle_input_labels,
            "physical_input_selected": self._handle_physical_input_selected,
            "current_source_content_aspect": self._handle_current_source_content_aspect,
            "detected_source_aspect": self._handle_detected_source_aspect,
            "source_mode": self._handle_source_mode,
            "source_vertical_rate": self._handle_source_vertical_rate,
            "source_dynamic_range": self._handle_source_dynamic_range,
        }
        self._subscribe_device_state_events()

    def __repr__(self):
        return f"<LumagenDevice id='{self.device_id}' at {self.host}:{self.port}>"

    def _subscribe_device_state_events(self):
        """Subscribe to device state updates from the dispatcher."""
        for attr_name in self._attr_handlers:
            self.dispatcher.register_listener(attr_name, self._create_event_callback(attr_name))

        self.dispatcher.register_listener(
            EventType.CONNECTION_STATE, self._handle_connection_state
        )

    def _create_event_callback(self, attr_name: str):
        """Create an async callback for attribute change events."""
        async def callback(event_data: dict):
            await self._on_device_state_event(attr_name, event_data)
        return lambda _, ed: asyncio.create_task(callback(ed))

    async def _on_device_state_event(self, attr_name: str, event_data: dict) -> None:
        """Dispatch state event to the appropriate handler."""
        value = event_data.get("value")
        _LOG.debug("State changed: %s -> %s", attr_name, value)

        handler = self._attr_handlers.get(attr_name)
        if handler:
            await handler(value)
        else:
            _LOG.debug("No handler registered for attribute: %s", attr_name)

    async def _handle_device_status(self, value: Any) -> None:
        """Handle updates to device power status."""
        try:
            self.current_status = PowerStateEnum(value)
            if self.current_status == PowerStateEnum.ACTIVE:
                self._attr_state = States.ON
            elif self.current_status == PowerStateEnum.STANDBY:
                self._attr_state = States.STANDBY
            else:
                self._attr_state = States.UNKNOWN
            await self._emit_update(EntityPrefix.MEDIA_PLAYER.value, MediaAttr.STATE, self._attr_state)
            await self._emit_update(EntityPrefix.REMOTE.value, MediaAttr.STATE, self._attr_state)
        except ValueError:
            _LOG.warning("Unknown power state received: %s", value)
            self.current_status = PowerStateEnum.UNKNOWN
            self._attr_state = States.UNKNOWN

    async def _handle_is_alive(self, _: Any) -> None:
        """Mark device as alive."""
        self._is_alive = True

    async def _handle_input_labels(self, value: Any) -> None:
        """Handle input label updates from the device."""
        await self._emit_update(EntityPrefix.MEDIA_PLAYER.value, MediaAttr.SOURCE_LIST, value)
        self._source_list = self.device.source_list
        _LOG.debug(self.source_list)

    async def _handle_physical_input_selected(self, value: Any) -> None:
        """Handle selection of a physical input."""
        try:
            index = int(value) - 1
            source_name = self._source_list[index] if 0 <= index < len(self._source_list) else None
            if source_name:
                self._active_source = source_name
                await self._emit_update(EntityPrefix.MEDIA_PLAYER.value, MediaAttr.SOURCE, source_name)
            else:
                _LOG.warning("Invalid physical_input_selected index: %s", value)
            await self._emit_update(EntityPrefix.PHYSICAL_INPUT_SELECTED.value, SensorAttr.VALUE, f"Input: {value}")
        except (ValueError, TypeError):
            _LOG.warning("Unable to process physical_input_selected value: %s", value)

    async def _handle_connection_state(self, _, event_data: dict) -> None:
        """Process connection state changes."""
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

            await asyncio.sleep(1)
            _LOG.debug("Fetching labels after connection...")
            await self.device.executor.get_labels(get_all=False)

    async def _handle_current_source_content_aspect(self, value: Any) -> None:
        _LOG.debug("Handle current_source_content_aspect.....................")
        _LOG.debug("Event received: %s", value)
        await self._emit_update(EntityPrefix.CURRENT_SOURCE_CONTENT_ASPECT.value, SensorAttr.VALUE, str(value))

    async def _handle_detected_source_aspect(self, value: Any) -> None:
        _LOG.debug("Handle detected_source_aspect.....................")
        _LOG.debug("Event received: %s", value)
        await self._emit_update(EntityPrefix.DETECTED_SOURCE_ASPECT.value, SensorAttr.VALUE, str(value))

    async def _handle_source_mode(self, value: Any) -> None:
        _LOG.debug("Handle source_mode.....................")
        _LOG.debug("Event received: %s", value)
        await self._emit_update(EntityPrefix.INPUT_MODE.value, SensorAttr.VALUE, str(value))

    async def _handle_source_vertical_rate(self, value: Any) -> None:
        _LOG.debug("Handle source_vertical_rate.....................")
        _LOG.debug("Event received: %s", value)
        await self._emit_update(EntityPrefix.INPUT_RATE.value, SensorAttr.VALUE, str(value))

    async def _handle_source_dynamic_range(self, value: Any) -> None:
        _LOG.debug("Handle source_dynamic_range.....................")
        _LOG.debug("Event received: %s", value)
        await self._emit_update(EntityPrefix.INPUT_FORMAT.value, SensorAttr.VALUE, str(value))

    async def _emit_update(self, prefix: str, attr: str, value: Any) -> None:
        entity_id = f"{prefix}.{self.device_id}"
        self.events.emit(Events.UPDATE.name, entity_id, {attr: value})

    # @property
    # def executor(self) -> CommandExecutor:
    #     """Return the command executor."""
    #     return self.context.connection.executor

    @property
    def device_info(self) -> DeviceInfo:
        """Get the DeviceInfo class."""
        return self.device.device_info

    @property
    def is_on(self) -> bool:
        """Return whether device is powered on."""
        return self.current_status == PowerStateEnum.ACTIVE

    # @property
    # def is_connected(self) -> bool:
    #     """Return whether device is connected."""
    #     return self.device.is_connected

    @property
    def is_alive(self) -> bool:
        """Return whether device is alive."""
        return self._is_alive

    @property
    def source_list(self) -> list[str]:
        """Return list of input sources."""
        return self._source_list

    @property
    def source(self) -> str:
        """Return currently active source."""
        return self._active_source

    @property
    def state(self) -> States:
        """Return current device state."""
        return self._attr_state

    @property
    def attributes(self) -> dict[str, any]:
        """Return device attributes dictionary."""
        updated_data = {
            MediaAttr.STATE: self.state,
        }
        if self.source_list:
            updated_data[MediaAttr.SOURCE_LIST] = self.source_list
        if self.source:
            updated_data[MediaAttr.SOURCE] = self.source
        return updated_data

    async def connect(self) -> bool:
        """Connect to the Lumagen device."""
        if self._connected:
            _LOG.debug("Already connected to Lumagen at %s:%d", self.host, self.port)
            return True

        #self.events.emit(Events.CONNECTING.name, self.device_id)

        try:
            await asyncio.wait_for(self.device.open(host=self.host, port=self.port), timeout=10)

            #if not self.discovery:
                #validate_simple_commands_exist_on_executor(SimpleCommands, self.executor, _LOG)

                #_LOG.debug("Fetching labels after connection...")
                #await self.device.executor.get_labels(get_all=False)

        except (OSError, ConnectionError, asyncio.exceptions.TimeoutError) as e:
            _LOG.error("Failed to connect to Lumagen at %s:%d - %s", self.host, self.port, e)
            return False

        return True

    async def disconnect(self):
        """Disconnect from the Lumagen device."""

        if self._connected:
            label = "IP2SL device" if self.discovery else "Lumagen"
            _LOG.debug("Disconnecting from %s at %s:%d",label, self.host, self.port)
            await self.device.close()

    async def send_command(self, command: str, parms = "") -> StatusCodes:
        """Send a named command to the device executor."""
        if not self._connected:
            _LOG.error("Connection not established.")
            return ucapi.StatusCodes.SERVICE_UNAVAILABLE
        return await self._execute_command(command, parms)

    async def _execute_command(
        self,
        command: str,
        parms: ParamType | ParamTuple | ParamDict | None = None
    ) -> ucapi.StatusCodes:
        """Dynamically invoke a command method from executor."""
        method = getattr(self.device.executor, command, None)
        if not callable(method):
            _LOG.warning("No executor method found for command: %s", command)
            return ucapi.StatusCodes.NOT_IMPLEMENTED

        try:
            sig = inspect.signature(method)
            # Handle methods with no parameters
            if len(sig.parameters) == 0:
                result = method()
            # Unpack parameters based on type
            elif isinstance(parms, (list, tuple)):
                result = method(*parms)
            elif isinstance(parms, dict):
                result = method(**parms)
            else:
                result = method(parms)

            # Await result if it's a coroutine
            if asyncio.iscoroutine(result):
                await result

            return ucapi.StatusCodes.OK
        except ValueError as err:
            _LOG.exception("Error executing command %s: %s", command, str(err))
            return ucapi.StatusCodes.BAD_REQUEST

    async def power_on(self) -> ucapi.StatusCodes:
        """Turn the device on."""
        if self.is_on:
            self._log_power_state_skip("on")
        else:
            await self.send_command("power_on")
        return ucapi.StatusCodes.OK

    async def power_off(self) -> ucapi.StatusCodes:
        """Turn the device off."""
        if self.is_on:
            await self.send_command("standby")
        else:
            self._log_power_state_skip("off")
        return ucapi.StatusCodes.OK

    def _log_power_state_skip(self, action: str):
        """Log when a power action is skipped because the device is already in the target state."""
        _LOG.debug("Power %s skipped: Device is already %s.", action, self.device.device_status)

    async def select_source(self, source: str) -> StatusCodes:
        """Set input source on the device."""
        if not source or source not in self.source_list:
            _LOG.warning("Invalid source: %s", source)
            return StatusCodes.BAD_REQUEST
        try:
            index = self.source_list.index(source)
            await self.device.executor.input(index)
            _LOG.info("Sent source select command for input %02d", index)
            return StatusCodes.OK
        except Exception as e:
            _LOG.error("Failed to select source '%s': %s", source, e)
            return StatusCodes.BAD_REQUEST

    async def get_info(self) -> LumagenInfo | None:
        """Query and return device info dataclass."""
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
