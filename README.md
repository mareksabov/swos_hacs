# MikroTik SwOS — Home Assistant Custom Integration

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-blue.svg?style=for-the-badge)](https://hacs.xyz/)
[![Latest release](https://img.shields.io/github/v/release/mareksabov/swos_hacs?style=for-the-badge&cacheSeconds=300)](https://github.com/mareksabov/swos_hacs/releases)
[![Downloads](https://img.shields.io/github/downloads/mareksabov/swos_hacs/total?style=for-the-badge&cacheSeconds=300)](https://github.com/mareksabov/swos_hacs/releases)
<!-- [![License](https://img.shields.io/github/license/mareksabov/swos_hacs?style=for-the-badge)](LICENSE) -->

Custom integration for **MikroTik SwOS** switches. It reads the internal endpoints `sys.b`, `link.b`, and `stats.b` via **HTTP Digest** and exposes sensors in Home Assistant.

> ✅ Tested on **CSS326-24G-2S+** with SwOS **2.18**. It should work with SwOS devices that return the `*.b` endpoints.

---

## ✨ Features

- Local polling via HTTP Digest (no cloud).
- Automatic value conversion:
  - IP → `ip_str` (e.g., `192.168.0.10`)
  <!-- - Uptime → `uptime_seconds` -->
  - Temperature → `temp_c`
- Base sensors (entities):
  - **SwOS temperature** (°C)
  <!-- - **SwOS uptime (s)** -->
  - **SwOS version**
  - **SwOS IP**
- Configurable **scan interval**.

> Note: Some SwOS builds return HTML for `!sys.b`/`!link.b`/`!stats.b`. This integration tries the standard endpoint first and only falls back to the `!…` variant if needed. Non-object (HTML) responses are ignored.

---

## ✅ Requirements

- SwOS with **HTTP access** enabled.
- A user/password for **HTTP Digest** authentication.
- Home Assistant can reach the SwOS IP/port (typically `80/tcp`).

---

## 🔧 Installation

### HACS (Custom repository)

1. In HACS → **Integrations** → **⋯ → Custom repositories** add:
   - **Repository**: `https://github.com/mareksabov/swos_hacs`
   - **Category**: *Integration*
2. Install **MikroTik SwOS**.
3. Restart Home Assistant.

### Manual (from Release ZIP)

1. **Download** the latest asset **`swos.zip`** from the [Releases](https://github.com/mareksabov/swos_hacs/releases) page.  
2. **Extract** it. You should end up with a folder named `swos` that contains files like `manifest.json`, `__init__.py`, etc.  
3. **Copy/replace** that folder to your HA config at:  
   ```
   <HA config>/custom_components/swos
   ```
   > The final path must be exactly `custom_components/swos` (not `custom_components/swos/swos`).  
   > Create the `custom_components` folder if it doesn’t exist.
4. **Restart Home Assistant.**  
5. (Optional) In **Settings → Devices & Services**, open *MikroTik SwOS* and click **Reload**.

**Upgrading manually:** delete the existing `custom_components/swos` folder, then repeat steps 1–4 with the new `swos.zip`.

## ⚙️ Configuration

1. **Settings → Devices & Services → Add Integration → MikroTik SwOS**
2. Enter:
   - **Host**: e.g., `192.168.0.10`
   - **Port**: `80` (change if you use a different port)
   - **Username** / **Password**
3. A device **SwOS <IP>** and sensors will be created.

### Options (after adding the integration)

- **Scan interval (s)** – default `30`.

---

## 🧩 Entities

<!--  
           | Entity           | Description               | Source key(s)                 |
           | ---------------- | ------------------------- | ----------------------------- |
           | SwOS IP          | Switch IP address         | `ip_str` / fallback `cip_str` |
           | SwOS temperature | Internal temperature (°C) | `temp_c` / fallback `temp`    |
           | SwOS uptime (s)  | Uptime in seconds         | `uptime_seconds` / `upt`      |
           | SwOS version     | SwOS firmware version     | `ver`                         |
           --> 

| Entity           | Description               | Source key(s)                 |
| ---------------- | ------------------------- | ----------------------------- |
| SwOS IP          | Switch IP address         | `ip_str` / fallback `cip_str` |
| SwOS temperature | Internal temperature (°C) | `temp_c` / fallback `temp`    |
| SwOS version     | SwOS firmware version     | `ver`                         |

> Tips: You can set MDI icons per-entity in the UI (or directly in `sensor.py` with `icon="mdi:..."`). Examples: `mdi:ip-network`, `mdi:thermometer`, `mdi:timer-outline`, `mdi:chip`.

---

## 🧪 Connectivity check (diagnostics)

From the HA terminal (SSH add-on):

```bash
# Without auth: expected 401 (confirms reachability)
wget -S -O- http://{ip-to-mikrotik-swos}/sys.b

# With Digest auth (or use curl --digest)
wget -S -O- --http-user='USERNAME' --http-password='PASSWORD' http://{ip-to-mikrotik-swos}/sys.b
curl --digest -u 'USERNAME':'PASSWORD' http://{ip-to-mikrotik-swos}/sys.b
```

A correct response looks like `{upt:0x..., ip:0x..., ver:'...' ...}` (not HTML).

---

## 🐞 Troubleshooting

**Entities show “Unknown”**
1. Enable debug logs:
   ```yaml
   logger:
     default: warning
     logs:
       custom_components.swos: debug
   ```
   Restart HA and watch **Settings → System → Logs** or run `ha core logs -f`.

2. Look for log lines like:
   - `httpx sys.b -> ... status=200, head='{upt:...}'` ✅
   - Seeing `<!doctype html...>` on `!sys.b` is fine — the integration ignores HTML and uses the data from the base endpoint.

**Integration logo does not appear**
- Home Assistant loads integration logos from the central **home-assistant/brands** repository. For custom integrations the logo in *Devices & Services* will not appear unless it’s in brands.  
- Per-entity icons can be set with MDI icons.

---

## 🗺️ Roadmap

- Per-port sensors (link up/down, speed, duplex) from `link.b`.
- RX/TX bytes & throughput from `stats.b` (combining high/low 32-bit registers).
- Diagnostic health sensor / service to trigger manual refresh.
- UI selection of monitored ports.

---

## 👨‍💻 Development

- Minimal files live under `custom_components/swos/*`.
- Dependencies are installed automatically via `manifest.json` (`httpx`, `requests`).

### Release steps (HACS)

1. Bump `version` in `custom_components/swos/manifest.json`.
2. Push changes to `main`.
3. Create a **GitHub release** with tag `vX.Y.Z` (HACS will pick it up).

Issues / PRs: https://github.com/mareksabov/swos_hacs/issues

---

## 📄 License

By contributing, you agree that your contributions will be licensed under its MIT License.

---
