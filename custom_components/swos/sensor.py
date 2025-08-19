
from __future__ import annotations

from typing import Optional, List, Any, Dict

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SwOSCoordinator


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: SwOSCoordinator = data["coordinator"]

    entities = [
        SwOSSimpleSensor(coordinator, entry.entry_id, "SwOS teplota", "sys", ["temp_c", "temp"], UnitOfTemperature.CELSIUS, "temperature", icon=None),
        SwOSSimpleSensor(coordinator, entry.entry_id, "SwOS uptime (s)", "sys", ["uptime_seconds", "upt"], None, None, icon="mdi:timer"),
        SwOSSimpleSensor(coordinator, entry.entry_id, "SwOS verzia", "sys", ["ver"], None, None, icon="mdi:chip"),
        SwOSSimpleSensor(coordinator, entry.entry_id, "SwOS IP", "sys", ["ip_str", "cip_str"], None, None, icon="mdi:ip"),
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
        keys: List[str],
        unit: Optional[str] = None,
        device_class: Optional[str] = None,
        icon: Optional[str] = None,
    ) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._section = section
        self._keys = keys
        self._attr_name = name
        self._attr_unique_id = f"{entry_id}_{section}_{'_'.join(keys)}"
        if unit:
            self._attr_native_unit_of_measurement = unit
        if device_class:
            self._attr_device_class = device_class
        if icon:
            self._attr_icon = icon

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success and (self._section in self.coordinator.data)

    @property
    def device_info(self) -> DeviceInfo:
        sys = self.coordinator.data.get("sys", {})
        ip = sys.get("ip_str") or sys.get("cip_str") or "unknown"
        identifiers = {(DOMAIN, f"swos_{ip}")}
        model = "MikroTik SwOS"
        name = f"SwOS {ip}"
        return DeviceInfo(
            identifiers=identifiers,
            manufacturer="MikroTik",
            model=model,
            name=name,
        )

    @property
    def native_value(self):
        data = self.coordinator.data.get(self._section, {})
        for k in self._keys:
            if k in data:
                return data[k]
        return None
