"""Constants for the Hunter Hydrawise integration."""
from datetime import timedelta
import logging

import voluptuous as vol

from homeassistant.const import CONF_ACCESS_TOKEN, CONF_SCAN_INTERVAL
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

ALLOWED_WATERING_TIME = [5, 10, 15, 30, 45, 60]

CONF_WATERING_TIME = "watering_minutes"

NOTIFICATION_ID = "hydrawise_notification"
NOTIFICATION_TITLE = "Hydrawise Setup"

DATA_HYDRAWISE = "hydrawise"
DOMAIN = "hydrawise"

SIGNAL_UPDATE_HYDRAWISE = "hydrawise_update"

DEFAULT_WATERING_TIME = 15
DEFAULT_SCAN_INTERVAL = timedelta(seconds=120)
DEFAULT_NAME_IMPORT = "configuration.yaml"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_ACCESS_TOKEN): cv.string,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): cv.time_period,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)
