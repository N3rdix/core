"""Config flow to configure the Hydrawise integration."""
from __future__ import annotations

from datetime import timedelta
from typing import Any

from hydrawiser.core import Hydrawiser
from requests.exceptions import ConnectTimeout, HTTPError

from homeassistant.config_entries import SOURCE_IMPORT, ConfigFlow
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    ALLOWED_WATERING_TIME,
    CONF_ACCESS_TOKEN,
    CONF_SCAN_INTERVAL,
    CONF_WATERING_TIME,
    DEFAULT_NAME_IMPORT,
    DOMAIN,
    cv,
    vol,
)

WATERING_SELECTOR = SelectSelector(
    SelectSelectorConfig(
        options=[
            str(interval)
            # SelectOptionDict(value=interval, label=interval)
            for interval in ALLOWED_WATERING_TIME
        ],
        mode=SelectSelectorMode.DROPDOWN,
    )
)

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ACCESS_TOKEN): cv.string,
        vol.Optional(CONF_WATERING_TIME): WATERING_SELECTOR,
        vol.Optional(CONF_SCAN_INTERVAL, default=120): cv.positive_int,
    }
)


def get_hydrawiser(access_token):
    """Get the Hydrawise API instance."""
    hydrawise = Hydrawiser(access_token)
    return hydrawise


class HYdrawiseFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a Comfoconnect config flow."""

    VERSION = 1

    # async def async_step_import(self, import_config: dict[str, Any]) -> FlowResult:
    #     """Import a config entry."""
    #     import_config = import_config.get(DOMAIN, import_config)

    #     for entry in self._async_current_entries():
    #         if entry.data[CONF_HOST] == import_config[CONF_HOST]:
    #             _LOGGER.warning(
    #                 "YAML config for ComfoConnect bridge on %s has been imported. Please remove it from your configuration.YAML",
    #                 import_config[CONF_HOST],
    #             )
    #             return self.async_abort(reason="already_configured")

    #     # Enhance with defaults if necessary
    #     import_config[CONF_NAME] = import_config.get(CONF_NAME, DEFAULT_NAME)
    #     import_config[CONF_TOKEN] = import_config.get(CONF_TOKEN, DEFAULT_TOKEN)
    #     import_config[CONF_PIN] = import_config.get(CONF_PIN, DEFAULT_PIN)
    #     import_config[CONF_USER_AGENT] = import_config.get(
    #         CONF_USER_AGENT, DEFAULT_USER_AGENT
    #     )

    #     return await self.async_step_user(import_config)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initiated by the user."""
        errors = {}
        if user_input is not None:
            access_token = user_input[CONF_ACCESS_TOKEN]
            scan_interval = timedelta(seconds=user_input[CONF_SCAN_INTERVAL])

            self._async_abort_entries_match({CONF_ACCESS_TOKEN: access_token})

            # Check if API returns a valid result
            try:
                # hydrawise = Hydrawiser(user_token=access_token)
                hydrawise = await self.hass.async_add_executor_job(
                    get_hydrawiser, access_token
                )

            except (ConnectTimeout, HTTPError):
                errors["base"] = "cannot_connect"
                return await self._show_setup_form(errors)

            title = (
                DEFAULT_NAME_IMPORT if self.source == SOURCE_IMPORT else hydrawise.name
            )

            return self.async_create_entry(
                title=title,
                data={
                    CONF_ACCESS_TOKEN: access_token,
                    CONF_SCAN_INTERVAL: scan_interval,
                },
            )

        return await self._show_setup_form(user_input)

    async def _show_setup_form(
        self, errors: dict[str, str] | None = None
    ) -> FlowResult:
        """Show the setup form to the user."""
        return self.async_show_form(
            step_id="user",
            data_schema=USER_SCHEMA,
            errors=errors or {},
        )
