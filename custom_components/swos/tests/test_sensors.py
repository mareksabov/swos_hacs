# custom_components/swos/tests/test_sensors.py
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import device_registry as dr

from custom_components.swos.const import DOMAIN


@pytest.mark.asyncio
async def test_async_setup_entry_creates_entities_and_device(
    hass, enable_custom_integrations, mock_coordinator_first_refresh
):
    """Overí načítanie integrácie, vytvorenie device a 4 senzorov + formát uptime."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "host": "192.168.0.10",
            "username": "admin",
            "password": "dummy",
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED

    # --- Device registry
    dev_reg = dr.async_get(hass)
    dev = dev_reg.async_get_device(identifiers={(DOMAIN, "swos_192.168.0.10")})
    assert dev is not None
    assert dev.manufacturer == "MikroTik"
    assert dev.model == "MikroTik SwOS"
    assert "SwOS 192.168.0.10" in (dev.name or "")

    # --- Sensor states (hľadáme podľa friendly_name)
    sensors_by_name = {s.name: s for s in hass.states.async_all("sensor")}

    # Uptime – formátovaný + raw atribút
    up = sensors_by_name["MikroTik SwOS uptime"]
    assert up.state == "0:01:01:01"
    assert up.attributes.get("seconds") == 366100
    # ikona z manifestu senzora
    assert up.attributes.get("icon") == "mdi:timer"

    # Teplota
    t = sensors_by_name["MikroTik SwOS temperature"]
    assert t.state == "42"
    # jednotka by mala byť °C
    assert t.attributes.get("unit_of_measurement") in ("°C", "C")  # podľa HA verzie

    # Verzia
    ver = sensors_by_name["MikroTik SwOS version"]
    assert ver.state == "2.13"

    # IP adresa
    ip = sensors_by_name["MikroTik SwOS IP"]
    assert ip.state == "192.168.0.10"
