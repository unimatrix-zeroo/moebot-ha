import logging

from homeassistant.components.lawn_mower import (
    LawnMowerEntity,
    LawnMowerEntityFeature,
    LawnMowerActivity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from pymoebot import MoeBot

from .const import DOMAIN
from . import BaseMoeBotEntity

_LOGGER = logging.getLogger(__name__)

_STATUS_TO_HA = {
    "STANDBY": LawnMowerActivity.DOCKED,
    "MOWING": LawnMowerActivity.MOWING,
    "FIXED_MOWING": LawnMowerActivity.MOWING,
    "PAUSED": LawnMowerActivity.PAUSED,
    "PARK": LawnMowerActivity.RETURNING,
    "CHARGING": LawnMowerActivity.DOCKED,
    "CHARGING_WITH_TASK_SUSPEND": LawnMowerActivity.DOCKED,
    "LOCKED": LawnMowerActivity.ERROR,
    "EMERGENCY": LawnMowerActivity.ERROR,
    "ERROR": LawnMowerActivity.ERROR,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MoeBot lawn mower entity."""
    moebot: MoeBot = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MoeBotMowerEntity(moebot)])


class MoeBotMowerEntity(BaseMoeBotEntity, LawnMowerEntity):
    """MoeBot lawn mower entity."""

    _attr_supported_features = (
        LawnMowerEntityFeature.START_MOWING
        | LawnMowerEntityFeature.PAUSE
        | LawnMowerEntityFeature.DOCK
    )

    _attr_icon = "mdi:robot-mower"

    def __init__(self, moebot: MoeBot) -> None:
        super().__init__(moebot)

        self._attr_unique_id = f"{moebot.id}_mower"
        self._attr_name = "MoeBot Mower"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, moebot.id)},
            manufacturer="MoeBot",
            name=f"MoeBot ({moebot.id})",
        )

        # Register push listener
        self._moebot.add_listener(self._handle_update)

    def _handle_update(self, raw_msg: dict) -> None:
        """Handle push updates from MoeBot (thread-safe)."""
        _LOGGER.debug("MoeBot update: %s", raw_msg)
        self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)

    @property
    def activity(self) -> LawnMowerActivity | None:
        """Return current mower activity."""
        return _STATUS_TO_HA.get(self._moebot.state)

    async def async_start_mowing(self) -> None:
        """Start mowing."""
        await self.hass.async_add_executor_job(self._moebot.start)

    async def async_pause(self) -> None:
        """Pause mowing."""
        await self.hass.async_add_executor_job(self._moebot.pause)

    async def async_dock(self) -> None:
        """Return to docking station."""
        await self.hass.async_add_execut
