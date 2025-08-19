import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.swos.const import DOMAIN
from custom_components.swos.formatters import DateTimeFormatterFromMiliseconds

pytestmark = pytest.mark.asyncio




def test_datetimeformatterfrommiliseconds():
    f = DateTimeFormatterFromMiliseconds()
    assert f.format(366100) == "0:01:01:01"


async def test_async_setup_entry(hass):
    """Test setup of the integration."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "host": "192.168.0.80",
            "username": "admin",
            "password": "NET@Kmaro#7806",
        },
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    device_reg = hass.helpers.device_registry.async_get(hass)
    assert any("SwOS" in str(d.name) for d in device_reg.devices.values())
