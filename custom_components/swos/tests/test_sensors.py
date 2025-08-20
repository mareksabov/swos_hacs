# custom_components/swos/tests/test_sensors.py
"""Tests for the SwOS sensors and device metadata handling."""


import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import EntityCategory
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC

from custom_components.swos.sensor import async_setup_entry
from custom_components.swos.const import DOMAIN


@pytest.mark.asyncio
async def test_async_setup_entry_creates_entities_and_device(
    hass, enable_custom_integrations, mock_coordinator_first_refresh
):
    """Verify integration setup, device creation and 4 sensors including uptime formatting."""
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

    # --- Sensor states (lookup by friendly_name)
    sensors_by_name = {s.name: s for s in hass.states.async_all("sensor")}

    # Uptime – formatted value + raw attribute
    up = sensors_by_name["MikroTik SwOS uptime"]
    assert up.state == "0:01:01:01"
    assert up.attributes.get("seconds") == 366100
    # sensor icon
    assert up.attributes.get("icon") == "mdi:timer"

    # Temperature
    t = sensors_by_name["MikroTik SwOS temperature"]
    assert t.state == "42"
    # unit should be Celsius (depends on HA version string)
    assert t.attributes.get("unit_of_measurement") in ("°C", "C")

    # Version
    ver = sensors_by_name["MikroTik SwOS version"]
    assert ver.state == "2.13"

    # IP address
    ip = sensors_by_name["MikroTik SwOS IP"]
    assert ip.state == "192.168.0.10"


class FakeCoordinator:
    def __init__(self, data):
        self.data = data
        self.last_update_success = True

    async def async_config_entry_first_refresh(self):
        # in tests we do not refresh, just simulate success
        return


@pytest.mark.asyncio
async def test_sensors_created_and_metadata(hass):
    # sys block used to build DeviceInfo and unique_id
    sys_block = {
        "ip_str": "192.168.0.123",
        "brd": "CRS326-24G-2S+",
        "ver": "2.16",
        "bld": "2024-11-01 10:20",
        "sid": "AB12C3D4E5",             # serial → primary stable id
        "mac": "AA-BB-CC-DD-EE-FF",      # includes dashes to test normalization
        "temp_c": 37,
        "uptime_seconds": 366100,        # seconds
    }
    coordinator = FakeCoordinator({"sys": sys_block})

    # fake entry and inject into hass.data same way as the integration does
    entry = type("E", (), {"entry_id": "test-entry"})()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"coordinator": coordinator}

    created = []
    def _add(entities):
        created.extend(entities)

    await async_setup_entry(hass, entry, _add)
    assert created, "Expected at least some sensors"

    # find sensors by their name
    def by_name(n):
        return next(e for e in created if e.name == n)

    temp = by_name("MikroTik SwOS temperature")
    uptime = by_name("MikroTik SwOS uptime")
    ver = by_name("MikroTik SwOS version")
    ip = by_name("MikroTik SwOS IP")

    # availability
    assert temp.available
    assert uptime.available
    assert ver.available
    assert ip.available

    # temperature: device_class + unit + value
    assert temp.device_class == SensorDeviceClass.TEMPERATURE
    assert temp.native_unit_of_measurement is not None  # CELSIUS
    assert temp.native_value == 37

    # uptime: formatted + extra raw attribute + DIAGNOSTIC category
    assert uptime.native_value == "0:01:01:01"
    attrs = uptime.extra_state_attributes
    assert attrs and attrs.get("seconds") == 366100
    assert uptime.entity_category == EntityCategory.DIAGNOSTIC

    # version + ip are diagnostic
    assert ver.entity_category == EntityCategory.DIAGNOSTIC
    assert ip.entity_category == EntityCategory.DIAGNOSTIC

    # unique_id uses stable id from serial number (sid)
    assert temp.unique_id.startswith("AB12C3D4E5_sys_")
    assert uptime.unique_id.startswith("AB12C3D4E5_sys_")

    # DeviceInfo from sys:
    di = temp.device_info
    # identifiers
    ids = di["identifiers"]
    assert any(t[0] == DOMAIN and t[1].startswith("swos_AB12C3D4E5") for t in ids)

    # name and model
    assert di["name"] == "SwOS 192.168.0.123"
    assert di["model"] == "CRS326-24G-2S+"

    # sw_version combined (ver + bld)
    assert di["sw_version"] == "2.16 (2024-11-01 10:20)"
    # serial_number
    assert di["serial_number"] == "AB12C3D4E5"
    # configuration_url only if IP known
    assert di["configuration_url"] == "http://192.168.0.123"

    # connections include normalized MAC (AA:BB:CC:DD:EE:FF)
    conns = di.get("connections")
    assert conns and (CONNECTION_NETWORK_MAC, "aa:bb:cc:dd:ee:ff") in conns


@pytest.mark.asyncio
async def test_fallbacks_when_sys_missing(hass):
    """When sys block is missing or minimal, entity is still available and DeviceInfo does not crash."""
    coordinator = FakeCoordinator({})  # without "sys"
    entry = type("E", (), {"entry_id": "no-sys"})()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"coordinator": coordinator}

    created = []
    def _add(entities):
        created.extend(entities)

    await async_setup_entry(hass, entry, _add)
    assert created

    temp = next(e for e in created if e.name == "MikroTik SwOS temperature")
    di = temp.device_info

    # fallback name and identifiers still present
    assert "identifiers" in di and di["identifiers"]
    assert di["name"].startswith("SwOS ")
    # configuration_url is None if IP unknown
    assert di.get("configuration_url") in (None, "http://unknown")
