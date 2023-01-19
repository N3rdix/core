"""Test ESPHome update entities."""
from unittest.mock import Mock, patch

import pytest

from homeassistant.components.esphome.dashboard import async_get_dashboard


@pytest.fixture(autouse=True)
def stub_reconnect():
    """Stub reconnect."""
    with patch("homeassistant.components.esphome.ReconnectLogic.start"):
        yield


@pytest.mark.parametrize(
    "devices_payload,expected_state,expected_attributes",
    [
        (
            [{"name": "test", "current_version": "1.2.3"}],
            "on",
            {"latest_version": "1.2.3", "installed_version": "1.0.0"},
        ),
        (
            [{"name": "test", "current_version": "1.0.0"}],
            "off",
            {"latest_version": "1.0.0", "installed_version": "1.0.0"},
        ),
        (
            [],
            "unavailable",
            {},
        ),
    ],
)
async def test_update_entity(
    hass,
    mock_config_entry,
    mock_device_info,
    mock_dashboard,
    devices_payload,
    expected_state,
    expected_attributes,
):
    """Test ESPHome update entity."""
    mock_dashboard["configured"] = devices_payload
    await async_get_dashboard(hass).async_refresh()

    mock_config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.esphome.update.DomainData.get_entry_data",
        return_value=Mock(available=True, device_info=mock_device_info),
    ):
        assert await hass.config_entries.async_forward_entry_setup(
            mock_config_entry, "update"
        )

    state = hass.states.get("update.none_firmware")
    assert state is not None
    assert state.state == expected_state
    for key, expected_value in expected_attributes.items():
        assert state.attributes.get(key) == expected_value
