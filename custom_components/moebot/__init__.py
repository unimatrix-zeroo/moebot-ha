"""The MoeBot integration."""
from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity, DeviceInfo

from pymoebot import MoeBot

from .const import DOMAIN

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.NUMBER,
    Platform.SWITCH,
    Platform.BUTTON,
    Platform.LAWN_MOWER,
]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up MoeBot from a config entry."""

    moebot = await hass.async_add_executor_job(
        MoeBot,
        entry.data["device_id"],
        entry.data["ip_address"],
        entry.data["local_key"],
    )

    _LOGGER.info("Created MoeBot device %s", moebot.id)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = moebot

    await hass.async_add_executor_job(moebot.listen)

    def _shutdown() -> None:
        _LOGGER.debug("Stopping MoeBot listener")
        moebot.unlisten()

    # Ensure clean shutdown on unload OR HA stop
    entry.async_on_unload(_shutdown)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        moebot: MoeBot = hass.data[DOMAIN].pop(entry.entry_id)
        moebot.unlisten()

    return unload_ok


class BaseMoeBotEntity(Entity):
    """Base entity for all MoeBot entities."""

    _attr_should_poll = False

    def __init__(self, moebot: MoeBot) -> None:
        self._moebot = moebot

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, moebot.id)}
        )

    @property
    def available(self) -> bool:
        return self._moebot.online

    @property
    def extra_state_attributes(self) -> dict | None:
        if self._moebot.last_update is not None:
            return {
                "last_message_received": datetime.fromtimestamp(
                    self._moebot.last_update
                )
            }
        return None

    async def async_added_to_hass(self) -> None:
        """Register MoeBot push listener."""

        def _listener(raw_msg: dict) -> None:
            _LOGGER.debug(
                "%s received update: %s",
                self.__class__.__name__,
                raw_msg,
            )
            # Thread-safe state update
            self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)

        self._moebot.add_listener(_listener)
