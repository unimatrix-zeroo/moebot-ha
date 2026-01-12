from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum

from homeassistant.components.number import (
    NumberEntity,
    NumberMode,
    NumberDeviceClass,
)
from homeassistant.helpers.entity import EntityCategory

from pymoebot import MoeBot, ZoneConfig

from . import BaseMoeBotEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up MoeBot number entities."""
    moebot: MoeBot = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[NumberEntity] = [WorkingTimeNumber(moebot)]

    for zone in range(1, 6):
        for part in ZoneNumberType:
            entities.append(ZoneConfigNumber(moebot, zone, part))

    async_add_entities(entities)


class MoeBotNumberBase(BaseMoeBotEntity, NumberEntity):
    """Base class for MoeBot numbers."""

    _attr_has_entity_name = True

    def __init__(self, moebot: MoeBot) -> None:
        super().__init__(moebot)
        self._moebot.add_listener(self._handle_update)

    def _handle_update(self, raw_msg: dict) -> None:
        self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)


class WorkingTimeNumber(MoeBotNumberBase):
    _attr_name = "Mowing Time"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = 1
    _attr_native_max_value = 12
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER
    _attr_device_class = NumberDeviceClass.DURATION
    _attr_native_unit_of_measurement = "h"

    def __init__(self, moebot: MoeBot) -> None:
        super().__init__(moebot)
        self._attr_unique_id = f"{moebot.id}_mow_time_hrs"

    @property
    def native_value(self) -> float | None:
        return self._moebot.mow_time

    async def async_set_native_value(self, value: float) -> None:
        await self.hass.async_add_executor_job(
            setattr, self._moebot, "mow_time", int(value)
        )


@dataclass(frozen=True)
class ZoneTypeData:
    type_name: str
    position: int


class ZoneNumberType(ZoneTypeData, Enum):
    DISTANCE = ("Distance", 0)
    RATIO = ("Ratio", 1)


class ZoneConfigNumber(MoeBotNumberBase):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = 0
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX
    _attr_entity_registry_enabled_default = False

    def __init__(self, moebot: MoeBot, zone: int, part: ZoneNumberType) -> None:
        super().__init__(moebot)
        self.zone = zone
        self.part = part

        self._attr_unique_id = (
            f"{moebot.id}_zone{zone}_{part.value.type_name.lower()}"
        )
        self._attr_name = f"Zone {zone} {part.value.type_name}"

        self._attr_native_max_value = (
            100 if part == ZoneNumberType.RATIO else 200
        )
        self._attr_native_unit_of_measurement = (
            "%" if part == ZoneNumberType.RATIO else "m"
        )
        self._attr_device_class = (
            NumberDeviceClass.DISTANCE
            if part == ZoneNumberType.DISTANCE
            else None
        )

    @staticmethod
    def _zone_config_to_list(zc: ZoneConfig) -> list[int]:
        return [
            int(zc.zone1[0]), int(zc.zone1[1]),
            int(zc.zone2[0]), int(zc.zone2[1]),
            int(zc.zone3[0]), int(zc.zone3[1]),
            int(zc.zone4[0]), int(zc.zone4[1]),
            int(zc.zone5[0]), int(zc.zone5[1]),
        ]

    @property
    def native_value(self) -> float | None:
        if not self._moebot.zones:
            _LOGGER.debug("Zone data not yet available")
            return None

        values = self._zone_config_to_list(self._moebot.zones)
        return values[(2 * (self.zone - 1)) + self.part.value.position]

    async def async_set_native_value(self, value: float) -> None:
        if not self._moebot.zones:
            return

        values = self._zone_config_to_list(self._moebot.zones)
        values[(2 * (self.zone - 1)) + self.part.value.position] = int(value)

        zc = ZoneConfig(*values)
        await self.hass.async_add_executor_job(
            setattr, self._moebot, "zones", zc
        )
