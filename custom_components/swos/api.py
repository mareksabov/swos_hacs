
from __future__ import annotations

import asyncio
import logging
import struct
from typing import Dict, Optional

import httpx
import requests
from requests.auth import HTTPDigestAuth

_LOGGER = logging.getLogger(__name__)


def _hexstr_to_ascii(s: str) -> str:
    try:
        return bytes.fromhex(s).decode("ascii", errors="ignore")
    except Exception:
        return s


def _hex_to_ip_le(vhex: int) -> str:
    try:
        b = struct.pack("<I", vhex)
        return ".".join(str(i) for i in b[::-1])
    except Exception:
        return str(vhex)


def _hex_to_mac(hexs: str) -> str:
    try:
        raw = bytes.fromhex(hexs)
        return ":".join(f"{b:02x}" for b in raw)
    except Exception:
        return hexs


def parse_swos_blob(text: str) -> Dict:
    t = text.strip()
    if t.startswith("{") and t.endswith("}"):
        t = t[1:-1]

    parts = []
    last = 0
    depth = 0
    for i, ch in enumerate(t):
        if ch == "," and depth == 0:
            parts.append(t[last:i])
            last = i + 1
        elif ch in "{}":
            depth += (1 if ch == "{" else -1)
    parts.append(t[last:])

    out = {}
    for p in parts:
        if ":" not in p:
            continue
        k, v = p.split(":", 1)
        key = k.strip()
        v = v.strip()

        if v.startswith("0x"):
            try:
                out[key] = int(v, 16)
            except ValueError:
                out[key] = v
        elif len(v) >= 2 and v[0] == "'" and v[-1] == "'":
            raw = v[1:-1]
            if key in ("ver", "id", "brd", "mrkt", "sid"):
                out[key] = _hexstr_to_ascii(raw)
            elif key in ("mac", "rmac"):
                out[key] = _hex_to_mac(raw)
            else:
                out[key] = raw
        else:
            out[key] = v

    # derived
    if "ip" in out and isinstance(out["ip"], int):
        out["ip_str"] = _hex_to_ip_le(out["ip"])
    if "cip" in out and isinstance(out["cip"], int):
        out["cip_str"] = _hex_to_ip_le(out["cip"])
    if "temp" in out and isinstance(out["temp"], int):
        out["temp_c"] = out["temp"]
    if "upt" in out and isinstance(out["upt"], int):
        out["uptime_seconds"] = out["upt"]

    return out


class SwOSClient:
    def __init__(self, host: str, username: str, password: str, port: int = 80) -> None:
        self._host = host
        self._port = port
        self._authx = httpx.DigestAuth(username, password)
        self._authr = HTTPDigestAuth(username, password)
        self._client: Optional[httpx.AsyncClient] = None

    def _url(self, endpoint: str) -> str:
        return f"http://{self._host}:{self._port}/{endpoint}"

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=10.0, headers={"Accept": "*/*"})
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def fetch_blob(self, endpoint: str) -> Optional[str]:
        url = self._url(endpoint)
        try:
            client = await self._ensure_client()
            r = await client.get(url, auth=self._authx)
            _LOGGER.debug("httpx %s -> %s bytes, status=%s", endpoint, len(r.text or ""), r.status_code)
            if r.status_code == 200 and r.text.strip():
                return r.text
        except Exception as err:
            _LOGGER.warning("httpx failed on %s: %s", endpoint, err)

        # Fallback to requests in thread (some SwOS builds are picky)
        def _req() -> Optional[str]:
            try:
                rr = requests.get(url, auth=self._authr, timeout=10)
                _LOGGER.debug("requests %s -> %s bytes, status=%s", endpoint, len(rr.text or ""), rr.status_code)
                if rr.status_code == 200 and rr.text.strip():
                    return rr.text
            except Exception as er:
                _LOGGER.error("requests fallback failed on %s: %s", endpoint, er)
            return None

        return await asyncio.to_thread(_req)

    async def fetch_sys(self) -> Dict:
        for ep in ("sys.b", "!sys.b"):
            text = await self.fetch_blob(ep)
            if text:
                return parse_swos_blob(text)
        raise RuntimeError("No sys.b endpoint found or auth failed")

    async def fetch_all(self) -> Dict:
        data = {}
        for ep in ("sys.b", "link.b", "stats.b", "!sys.b", "!link.b", "!stats.b"):
            text = await self.fetch_blob(ep)
            if not text:
                continue
            key = ep.replace("!", "").split(".", 1)[0]
            try:
                data[key] = parse_swos_blob(text)
            except Exception:
                data[key] = {"raw": text}
        return data
