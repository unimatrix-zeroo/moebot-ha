from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE
from homeassistant.helpers.entity import EntityCategory

from pymoebot import MoeBot

from . import BaseMoeBotEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up MoeBot sensors."""
    moebot: MoeBot = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities(
        [
            MowingStateSensor(moebot),
            EmergencyStateSensor(moebot),
            WorkModeSensor(moebot),
            BatterySensor(moebot),
            PyMoebotVersionSensor(moebot),
            TuyaVersionSensor(moebot),
        ]
    )


class MoeBotSensorBase(BaseMoeBotEntity, SensorEntity):
    """Base class for MoeBot sensors."""

    _attr_has_entity_name = True

    def __init__(self, moebot: MoeBot) -> None:
        super().__init__(moebot)
        self._moebot.add_listener(self._handle_update)

    def _handle_update(self, raw_msg: dict) -> None:
        """Handle push update (thread-safe)."""
        self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)


class MowingStateSensor(MoeBotSensorBase):
    _attr_unique_id = None
    _attr_name = "Mowing State"

    def __init__(self, moebot: MoeBot) -> None:
        super().__init__(moebot)
        self._attr_unique_id = f"{moebot.id}_state"

    @property
    def native_value(self) -> str | None:
        return self._moebot.state


class EmergencyStateSensor(MoeBotSensorBase):
    _attr_name = "Emergency State"

    def __init__(self, moebot: MoeBot) -> None:
        super().__init__(moebot)
        self._attr_unique_id = f"{moebot.id}_emergency_state"

    @property
    def native_value(self) -> str | None:
        return self._moebot.emergency_state


class WorkModeSensor(MoeBotSensorBase):
    _attr_name = "Work Mode"

    def __init__(self, moebot: MoeBot) -> None:
        super().__init__(moebot)
        self._attr_unique_id = f"{moebot.id}_work_mode"

    @property
    def native_value(self) -> str | None:
        return self._moebot.work_mode


class BatterySensor(MoeBotSensorBase):
    _attr_name = "Battery"
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, moebot: MoeBot) -> None:
        super().__init__(moebot)
        self._attr_unique_id = f"{moebot.id}_battery"

    @property
    def native_value(self) -> int | None:
        return round(self._moebot.battery)


class PyMoebotVersionSensor(MoeBotSensorBase):
    _attr_name = "pymoebot Version"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, moebot: MoeBot) -> None:
        super().__init__(moebot)
        self._attr_unique_id = f"{moebot.id}_pymoebot_version"

    @property
    def native_value(self) -> str | None:
        return self._moebot.pymoebot_version


class TuyaVersionSensor(MoeBotSensorBase):
    _attr_name = "Tuya Protocol Version"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, moebot: MoeBot) -> None:
        super().__init__(moebot)
        self._attr_unique_id = f"{moebot.id}_tuya_version"

    @property
    def native_value(self) -> str | None:
        return self._moebot.tuya_version
