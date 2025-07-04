"""
Sensor entity functions.

:copyright: (c) 2023 by Unfolded Circle ApS.
:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from device import LumagenInfo
from ucapi.sensor import Attributes, DeviceClasses, Options, Sensor, States

_LOG = logging.getLogger(__name__)

class LumagenSensor(Sensor):
    """Representation of a Lumagen Sensor entity."""

    def __init__(self, info: LumagenInfo, sensor: str):
        """Initialize a Lumagen Sensor entity."""
        entity_id = f"{sensor}.{info.id}"
        name = info.name + " " + sensor.replace("_", " ")#f"{info.name} #{sensor.replace("_", " ")}".title()

        attributes = {
            Attributes.STATE: States.UNKNOWN,
            Attributes.VALUE: "unknown",
            Attributes.UNIT: "unknown",
        }

        options = { Options.DECIMALS: 1}

        super().__init__(
            identifier=entity_id,
            name=name.title(),
            features=[],
            attributes=attributes,
            device_class=DeviceClasses.CUSTOM,
            options=options
        )

        _LOG.debug("Lumagen Sensor init %s : %s", entity_id, attributes)

    def filter_changed_attributes(self, update: dict[str, Any]) -> dict[str, Any]:
        """
        Filter the given attributes and return only the changed values.

        :param update: dictionary with attributes.
        :return: filtered entity attributes containing changed attributes only.
        """

        attributes = {}

        for key in (Attributes.STATE, Attributes.VALUE):
            if key in update and key in self.attributes:
                if update[key] != self.attributes[key]:
                    attributes[key] = update[key]

        if Attributes.STATE in attributes:
            if attributes[Attributes.STATE] == States.UNKNOWN:
                attributes[Attributes.VALUE] = "none"

        if attributes:
            _LOG.debug("Lumagen Sensor update attributes %s -> %s", update, attributes)

        return attributes
