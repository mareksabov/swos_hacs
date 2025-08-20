from __future__ import annotations

from typing import Optional, List, Any, Dict

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC

from .const import DOMAIN
from .coordinator import SwOSCoordinator

from .formatters import BaseFormatter, DateTimeFormatterFromMiliseconds

# ----------------------------
# Setup
# ----------------------------
def _stable_id_from_sys(sysd: dict) -> str | None:
    serial = sysd.get("sid")
    mac = (sysd.get("mac") or sysd.get("rmac") or "")
    mac = mac.lower().replace(":", "").replace("-", "")
    return serial or mac or None
    
async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: SwOSCoordinator = data["coordinator"]

    await coordinator.async_config_entry_first_refresh()

    entities: List[SensorEntity] = [
        # Temperature (native numeric)
        SwOSSimpleSensor(
            coordinator,
            entry.entry_id,
            "MikroTik SwOS temperature",
            "sys",
            ["temp_c", "temp"],
            UnitOfTemperature.CELSIUS,
            device_class=SensorDeviceClass.TEMPERATURE,
            icon=None,
        ),
        # Uptime formatted via formatter, with raw seconds exposed as an attribute
        SwOSFormattedSensor(
            coordinator,
            entry.entry_id,
            "MikroTik SwOS uptime",
            "sys",
            ["uptime_seconds", "upt"],
            formatter=DateTimeFormatterFromMiliseconds(),
            #raw seconds is in centiseconds instead of seconds. This should be addressed.
            raw_attribute_name="seconds",
            icon="mdi:timer",
            entity_category=EntityCategory.DIAGNOSTIC,
        ),
        # Version (string)
        SwOSSimpleSensor(
            coordinator,
            entry.entry_id,
            "MikroTik SwOS version",
            "sys",
            ["ver"],
            None,
            None,
            icon="mdi:chip",
            entity_category=EntityCategory.DIAGNOSTIC,
        ),
        # IP address (string)
        SwOSSimpleSensor(
            coordinator,
            entry.entry_id,
            "MikroTik SwOS IP",
            "sys",
            ["ip_str", "cip_str"],
            None,
            None,
            icon="mdi:ip",
            entity_category=EntityCategory.DIAGNOSTIC,
        )      
    ]

    async_add_entities(entities)


# ----------------------------
# Base simple sensor
# ----------------------------
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
        entity_category: EntityCategory | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._section = section
        self._keys = keys
        self._attr_name = name

        sysd = coordinator.data.get("sys", {}) or {}
        stable = _stable_id_from_sys(sysd) or entry_id
        self._attr_unique_id = f"{stable}_{section}_{'_'.join(keys)}"

        if unit:
            self._attr_native_unit_of_measurement = unit
        if device_class:
            self._attr_device_class = device_class
        if icon:
            self._attr_icon = icon
        if entity_category:
            self._attr_entity_category = entity_category

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success and (self._section in self.coordinator.data)

    @property
    def device_info(self) -> DeviceInfo:
        sysd = self.coordinator.data.get("sys", {}) or {}

        ip = sysd.get("ip_str") or sysd.get("cip_str") or "unknown"
        model = sysd.get("brd") or "MikroTik SwOS"
        sw_ver = sysd.get("ver")
        bld = sysd.get("bld")
        serial = sysd.get("sid")
        raw_mac = (sysd.get("mac") or sysd.get("rmac") or "")
        mac = raw_mac.lower().replace("-", ":")

        config_url = f"http://{ip}" if ip != "unknown" else None
        
        stable_id = serial or mac or ip

        sw_version = f"{sw_ver} ({bld})" if sw_ver and bld else sw_ver 
        connections = {(CONNECTION_NETWORK_MAC, mac)} if mac else None

        return DeviceInfo(
            identifiers={(DOMAIN, f"swos_{stable_id}")},
            manufacturer="MikroTik",
            model=model,
            name=f"SwOS {ip}",
            configuration_url=config_url,
            sw_version=sw_version,
            serial_number=serial,
            connections=connections,
        )

    def _base_value(self) -> Any:
        data = self.coordinator.data.get(self._section, {})
        for k in self._keys:
            if k in data:
                return data[k]
        return None

    @property
    def native_value(self):
        return self._base_value()


# ----------------------------
# Generic formatted sensor
# ----------------------------
class SwOSFormattedSensor(SwOSSimpleSensor):
    """A generic sensor that takes the raw value from SwOSSimpleSensor and applies a formatter.

    formatter(value, data) -> formatted_value
    - value: the raw value selected from `keys`
    - data: the entire section dict (e.g., `coordinator.data['sys']`) for context

    If `raw_attribute_name` is provided, the original raw value is exposed as an attribute.
    """

    def __init__(
        self,
        coordinator: SwOSCoordinator,
        entry_id: str,
        name: str,
        section: str,
        keys: List[str],
        formatter: BaseFormatter = None,
        icon: Optional[str] = None,
        raw_attribute_name: Optional[str] = None,
        entity_category: EntityCategory | None = None,
    ) -> None:
        super().__init__(
            coordinator,
            entry_id,
            name,
            section,
            keys,
            unit=None,
            device_class=None,
            icon=icon,
            entity_category=entity_category,
        )
        self._formatter = formatter
        self._raw_attr = raw_attribute_name

    @property
    def native_value(self):
        raw = self._base_value()
        if self._formatter is None:
            return raw
        try:
            # data = self.coordinator.data.get(self._section, {})
            # return self._formatter(raw, data)
            return self._formatter.format(raw)
        except Exception:
            # Fallback to raw value on any formatter error
            return raw

    @property
    def extra_state_attributes(self) -> Dict[str, Any] | None:
        if not self._raw_attr:
            return None
        raw = self._base_value()
        return {self._raw_attr: raw}
