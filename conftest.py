# conftest.py (top-level)
import pytest

# zapne načítanie integrácie z custom_components/
pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture
def mock_coordinator_first_refresh(monkeypatch):
    """Nahradí prvé aj ďalšie refresh volania koordinatora tak,
    aby vracal stabilné dáta bez sieťových requestov.
    """
    async def _fake_update(self):
        return {
            "sys": {
                "temp_c": 42,
                "uptime_seconds": 366100,  # 366100 // 100 = 3661 s => 0:01:01:01
                "ver": "2.13",
                "ip_str": "192.168.0.10",
            }
        }

    monkeypatch.setattr(
        "custom_components.swos.coordinator.SwOSCoordinator._async_update_data",
        _fake_update,
    )
