from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.vacuum import (
    VacuumEntity,
    VacuumEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.icon import icon_for_battery_level

from pymoebot import MoeBot

from . import BaseMoeBotEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

_STATUS_TO_HA = {
    "STANDBY": "docked",
    "MOWING": "cleaning",
    "FIXED_MOWING": "cleaning",
    "PAUSED": "idle",
    "PARK": "returning",
    "CHARGING": "docked",
    "CHARGING_WITH_TASK_SUSPEND": "docked",
    "LOCKED": "error",
    "EMERGENCY": "error",
    "ERROR": "error",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    moebot: MoeBot = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MoeBotVacuumEntity(moebot)])


class MoeBotVacuumEntity(BaseMoeBotEntity, VacuumEntity):
    """Legacy vacuum entity (deprecated)."""

    _attr_supported_features = (
        VacuumEntityFeature.START
        | VacuumEntityFeature.PAUSE
        | VacuumEntityFeature.STOP
        | VacuumEntityFeature.RETURN_HOME
        | VacuumEntityFeature.BATTERY
    )

    _attr_icon = "mdi:robot-mower"

    def __init__(self, moebot: MoeBot) -> None:
        super().__init__(moebot)
        self._attr_unique_id = f"{moebot.id}_vacuum"
        self._attr_name = "MoeBot (Legacy Vacuum)"

        self._moebot.add_listener(self._handle_update)

    def _handle_update(self, raw_msg: dict) -> None:
        self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)

    @property
    def state(self) -> str | None:
        return _STATUS_TO_HA.get(self._moebot.state)

    @property
    def battery_level(self) -> int | None:
        return round(self._moebot.battery)

    @property
    def battery_icon(self) -> str:
        charging = self._moebot.state in (
            "CHARGING",
            "CHARGING_WITH_TASK_SUSPEND",
        )
        return icon_for_battery_level(self.battery_level, charging)

    async def async_start(self) -> None:
        await self.hass.async_add_executor_job(self._moebot.start)

    async def async_pause(self) -> None:
        await self.hass.async_add_executor_job(self._moebot.pause)

    async def async_stop(self, **kwargs: Any) -> None:
        await self.hass.async_add_executor_job(self._moebot.cancel)

    async def async_return_to_base(self, **kwargs: Any) -> None:
        await self.hass.async_add_executor_job(self._moebot.dock)
