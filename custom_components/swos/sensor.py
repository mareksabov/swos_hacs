
from __future__ import annotations

from typing import Optional

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SwOSCoordinator


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: SwOSCoordinator = data["coordinator"]

    entities = [
        SwOSSimpleSensor(coordinator, entry.entry_id, "SwOS teplota", "sys", "temp_c", UnitOfTemperature.CELSIUS, "temperature", icon=None),
        SwOSSimpleSensor(coordinator, entry.entry_id, "SwOS uptime (s)", "sys", "uptime_seconds", None, None, icon="mdi:timer"),
        SwOSSimpleSensor(coordinator, entry.entry_id, "SwOS verzia", "sys", "ver", None, None, icon="mdi:chip"),
        SwOSSimpleSensor(coordinator, entry.entry_id, "SwOS IP", "sys", "ip_str", None, None, icon="mdi:ip"),
    ]

    async_add_entities(entities)


class SwOSSimpleSensor(CoordinatorEntity[SwOSCoordinator], SensorEntity):
    _attr_has_entity_name = False

    def __init__(
        self,
        coordinator: SwOSCoordinator,
        entry_id: str,
        name: str,
        section: str,
        key: str,
        unit: Optional[str] = None,
        device_class: Optional[str] = None,
        icon: Optional[str] = None,
    ) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._section = section
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{entry_id}_{section}_{key}"
        if unit:
            self._attr_native_unit_of_measurement = unit
        if device_class:
            self._attr_device_class = device_class
        if icon:
            self._attr_icon = icon

    @property
    def device_info(self) -> DeviceInfo:
        sys = self.coordinator.data.get("sys", {})
        identifiers = {(DOMAIN, f"swos_{sys.get('ip_str', 'unknown')}")}
        model = "MikroTik SwOS"
        name = f"SwOS {sys.get('ip_str', '')}"
        return DeviceInfo(
            identifiers=identifiers,
            manufacturer="MikroTik",
            model=model,
            name=name,
        )

    @property
    def native_value(self):
        data = self.coordinator.data.get(self._section, {})
        return data.get(self._key)
