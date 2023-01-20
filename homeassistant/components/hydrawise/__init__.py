"""Support for Hydrawise cloud."""
from datetime import timedelta

from hydrawiser.core import Hydrawiser
from requests.exceptions import ConnectTimeout, HTTPError

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.dispatcher import async_dispatcher_connect, dispatcher_send
from homeassistant.helpers.entity import Entity, EntityDescription
from homeassistant.helpers.event import track_time_interval
from homeassistant.helpers.issue_registry import IssueSeverity, async_create_issue
from homeassistant.helpers.typing import ConfigType

from .const import (
    _LOGGER,
    CONF_ACCESS_TOKEN,
    CONF_SCAN_INTERVAL,
    DOMAIN,
    SIGNAL_UPDATE_HYDRAWISE,
)

PLATFORMS = [Platform.SWITCH, Platform.BINARY_SENSOR, Platform.SENSOR]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Hunter Hydrawise component."""
    # conf = config[DOMAIN]
    # access_token = conf[CONF_ACCESS_TOKEN]
    # scan_interval = conf.get(CONF_SCAN_INTERVAL)

    # try:
    #     hydrawise = Hydrawiser(user_token=access_token)
    #     hass.data[DATA_HYDRAWISE] = HydrawiseHub(hydrawise)
    # except (ConnectTimeout, HTTPError) as ex:
    #     _LOGGER.error("Unable to connect to Hydrawise cloud service: %s", str(ex))
    #     persistent_notification.async_create(
    #         hass,
    #         f"Error: {ex}<br />You will need to restart hass after fixing.",
    #         title=NOTIFICATION_TITLE,
    #         notification_id=NOTIFICATION_ID,
    #     )
    #     return False

    # def hub_refresh(event_time):
    #     """Call Hydrawise hub to refresh information."""
    #     _LOGGER.debug("Updating Hydrawise Hub component")
    #     hass.data[DATA_HYDRAWISE].data.update_controller_info()
    #     dispatcher_send(hass, SIGNAL_UPDATE_HYDRAWISE)

    # # Call the Hydrawise API to refresh updates
    # track_time_interval(hass, hub_refresh, scan_interval)

    conf = config.get(DOMAIN)
    if conf is None:
        return True

    _LOGGER.warning(
        "Configuring Hunter Hydrawise using YAML is being removed. Your existing "
        "YAML configuration has been imported into the UI automatically. Remove "
        "the Hunter Hydrawise YAML configuration from your configuration.yaml file and "
        "restart Home Assistant to fix this issue"
    )

    async_create_issue(
        hass,
        DOMAIN,
        "deprecated_yaml",
        breaks_in_ha_version="2023.6.0",
        is_fixable=False,
        severity=IssueSeverity.WARNING,
        translation_key="deprecated_yaml",
    )

    # Already imported, then quit
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.source == SOURCE_IMPORT:
            return True

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][SOURCE_IMPORT] = conf

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data=config,
        )
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the Hunter Hydrawise bridge."""

    access_token = entry.data[CONF_ACCESS_TOKEN]
    scan_interval_str = str(entry.data.get(CONF_SCAN_INTERVAL))
    scan_interval = timedelta(seconds=float(scan_interval_str))

    try:
        hydrawise = Hydrawiser(user_token=access_token)
        hub = HydrawiseHub(hydrawise)
    except (ConnectTimeout, HTTPError) as ex:
        _LOGGER.error("Unable to connect to Hydrawise cloud service: %s", str(ex))
        # persistent_notification.async_create(
        #     hass,
        #     f"Error: {ex}<br />You will need to restart hass after fixing.",
        #     title=NOTIFICATION_TITLE,
        #     notification_id=NOTIFICATION_ID,
        # )
        raise ConfigEntryNotReady from ex

    def hub_refresh(event_time):
        """Call Hydrawise hub to refresh information."""
        _LOGGER.debug("Updating Hydrawise Hub component")
        hass.data[DOMAIN].data.update_controller_info()
        dispatcher_send(hass, SIGNAL_UPDATE_HYDRAWISE)

    # Call the Hydrawise API to refresh updates
    track_time_interval(hass, hub_refresh, scan_interval)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = hub

    # Load platforms
    # await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Comfoconnect config entry."""

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class HydrawiseHub:
    """Representation of a base Hydrawise device."""

    def __init__(self, data):
        """Initialize the entity."""
        self.data = data


class HydrawiseEntity(Entity):
    """Entity class for Hydrawise devices."""

    _attr_attribution = "Data provided by hydrawise.com"

    def __init__(self, data, description: EntityDescription):
        """Initialize the Hydrawise entity."""
        self.entity_description = description
        self.data = data
        self._attr_name = f"{self.data['name']} {description.name}"

    async def async_added_to_hass(self):
        """Register callbacks."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_UPDATE_HYDRAWISE, self._update_callback
            )
        )

    @callback
    def _update_callback(self):
        """Call update method."""
        self.async_schedule_update_ha_state(True)

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {"identifier": self.data.get("relay")}
