from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import EntityCategory

from pymoebot import MoeBot

from . import BaseMoeBotEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up MoeBot switch entities."""
    moebot: MoeBot = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([ParkWhenRainingSwitch(moebot)])


class ParkWhenRainingSwitch(BaseMoeBotEntity, SwitchEntity):
    """Switch to control parking behavior when raining."""

    _attr_has_entity_name = True
    _attr_name = "Park If Raining"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, moebot: MoeBot) -> None:
        super().__init__(moebot)
        self._attr_unique_id = f"{moebot.id}_park_if_raining"
        self._moebot.add_listener(self._handle_update)

    def _handle_update(self, raw_msg: dict) -> None:
        """Handle push updates (thread-safe)."""
        self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)

    @property
    def is_on(self) -> bool:
        return bool(self._moebot.mow_in_rain)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.hass.async_add_executor_job(
            setattr, self._moebot, "mow_in_rain", True
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.hass.async_add_executor_job(
            setattr, self._moebot, "mow_in_rain", False
        )
