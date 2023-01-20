"""Support for Hydrawise sprinkler sensors."""
from __future__ import annotations

from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_MONITORED_CONDITIONS, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import dt

from . import HydrawiseEntity
from .const import _LOGGER, DOMAIN, cv, vol

SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="next_cycle",
        name="Next Cycle",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="watering_time",
        name="Watering Time",
        icon="mdi:water-pump",
        native_unit_of_measurement=UnitOfTime.MINUTES,
    ),
)

SENSOR_KEYS: list[str] = [desc.key for desc in SENSOR_TYPES]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_MONITORED_CONDITIONS, default=SENSOR_KEYS): vol.All(
            cv.ensure_list, [vol.In(SENSOR_KEYS)]
        )
    }
)

TWO_YEAR_SECONDS = 60 * 60 * 24 * 365 * 2
# WATERING_TIME_ICON = "mdi:water-pump"


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up a sensor for a Hydrawise device."""
    # hydrawise = hass.data[DATA_HYDRAWISE].data
    # monitored_conditions = config[CONF_MONITORED_CONDITIONS]

    # entities = [
    #     HydrawiseSensor(zone, description)
    #     for zone in hydrawise.relays
    #     for description in SENSOR_TYPES
    #     if description.key in monitored_conditions
    # ]

    # async_add_entities(entities, True)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up a sensor for a Hydrawise device."""
    hydrawise = hass.data[DOMAIN][entry.entry_id].data

    # For user input from config flow
    async_add_entities(
        [
            HydrawiseSensor(hydrawise, description)
            for zone in hydrawise.relays
            for description in SENSOR_TYPES
        ],
        True,
    )


class HydrawiseSensor(HydrawiseEntity, SensorEntity):
    """A sensor implementation for Hydrawise device."""

    def update(self) -> None:
        """Get the latest data and updates the states."""
        mydata = self.hass.data[DOMAIN].data
        _LOGGER.debug("Updating Hydrawise sensor: %s", self.name)
        relay_data = mydata.relays[self.data["relay"] - 1]
        if self.entity_description.key == "watering_time":
            if relay_data["timestr"] == "Now":
                self._attr_native_value = int(relay_data["run"] / 60)
            else:
                self._attr_native_value = 0
        else:  # _sensor_type == 'next_cycle'
            next_cycle = min(relay_data["time"], TWO_YEAR_SECONDS)
            _LOGGER.debug("New cycle time: %s", next_cycle)
            self._attr_native_value = dt.utc_from_timestamp(
                dt.as_timestamp(dt.now()) + next_cycle
            )
