from __future__ import annotations

from homeassistant.components.button import (
    ButtonEntity,
    ButtonDeviceClass,
)
from homeassistant.helpers.entity import EntityCategory

from pymoebot import MoeBot

from . import BaseMoeBotEntity
from .const import DOMAIN


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up MoeBot button entities."""
    moebot: MoeBot = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([PollDeviceButton(moebot)])


class PollDeviceButton(BaseMoeBotEntity, ButtonEntity):
    """Button to manually poll the MoeBot device."""

    _attr_has_entity_name = True
    _attr_name = "Poll Device"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = ButtonDeviceClass.UPDATE

    def __init__(self, moebot: MoeBot) -> None:
        super().__init__(moebot)
        self._attr_unique_id = f"{moebot.id}_poll_device"

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.hass.async_add_executor_job(self._moebot.poll)
