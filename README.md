
# MikroTik SwOS – HACS Custom Integration

Custom integration that polls SwOS (`sys.b`, `link.b`, `stats.b`) via HTTP Digest
and exposes sensors in Home Assistant (temperature, uptime, version, IP).

## Install
1. Copy `custom_components/swos` to your Home Assistant `config/custom_components/swos/`.
   Or add this repository as a HACS custom repository (Integration).
2. Restart Home Assistant.
3. Go to **Settings → Devices & Services → Add Integration → MikroTik SwOS**.
4. Enter host, username, password.

## Notes
- Requires internet access to install `httpx` (declared in `manifest.json`).
- Poll interval configurable in integration options.
- Ports/traffic can be added later (link.b/stats.b parser).

