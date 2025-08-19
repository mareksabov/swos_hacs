from __future__ import annotations

from typing import Optional, List, Any, Dict, Callable

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SwOSCoordinator

from .formatters import BaseFormatter, DateTimeFormatterFromMiliseconds

# ----------------------------
# Reusable formatters
# ----------------------------

# def fmt_dhms(value: Any, data: Dict[str, Any]) -> Optional[str]:
#     """Format seconds as dd:hh:mm:ss (days not zero-padded)."""
#     if value is None:
#         return None
#     try:
#         seconds = int(value)
#     except (TypeError, ValueError):
#         return None
#     if seconds < 0:
#         seconds = 0
#     days, rem = divmod(seconds, 24 * 3600)
#     hours, rem = divmod(rem, 3600)
#     minutes, secs = divmod(rem, 60)
#     return f"{days}:{hours:02d}:{minutes:02d}:{secs:02d}"

# def make_map_formatter(mapping: Dict[Any, Any]) -> Callable[[Any, Dict[str, Any]], Any]:
#     """Return a formatter that maps raw values using a dict (fallback to original)."""
#     def _fmt(value: Any, data: Dict[str, Any]) -> Any:
#         return mapping.get(value, value)
#     return _fmt

# def fmt_popcount(value: Any, data: Dict[str, Any]) -> Optional[int]:
#     """Count set bits in an integer mask (e.g., port bitmask)."""
#     if value is None:
#         return None
#     try:
#         v = int(value)
#     except (TypeError, ValueError):
#         return None
#     try:
#         return v.bit_count()
#     except AttributeError:
#         # Python <3.8 fallback (not needed in modern HA, but kept harmless)
#         return bin(v).count("1")


# ----------------------------
# Setup
# ----------------------------
async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: SwOSCoordinator = data["coordinator"]

    entities: List[SensorEntity] = [
        # Temperature (native numeric)
        SwOSSimpleSensor(
            coordinator,
            entry.entry_id,
            "MikroTik SwOS temperature",
            "sys",
            ["temp_c", "temp"],
            UnitOfTemperature.CELSIUS,
            "temperature",
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
            raw_attribute_name="seconds",
            icon="mdi:timer",
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
