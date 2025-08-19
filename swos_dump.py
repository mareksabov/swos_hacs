#!/usr/bin/env python3
import argparse, json, struct
import requests
from requests.auth import HTTPDigestAuth

def hexstr_to_ascii(s):
    try: return bytes.fromhex(s).decode("ascii", errors="ignore")
    except: return s

def hex_to_ip_le(vhex_int):
    try:
        b = struct.pack("<I", vhex_int)
        return ".".join(str(i) for i in b)  # 0x5000a8c0 -> 192.168.0.80
    except:
        return str(vhex_int)

def hex_to_mac(s):
    try: return ":".join(f"{b:02x}" for b in bytes.fromhex(s))
    except: return s

def parse_swos_blob(text):
    t = text.strip()
    if t.startswith("{") and t.endswith("}"):
        t = t[1:-1]
    parts, last, depth = [], 0, 0
    for i, ch in enumerate(t):
        if ch == "," and depth == 0:
            parts.append(t[last:i]); last = i+1
        elif ch in "{}":
            depth += 1 if ch == "{" else -1
    parts.append(t[last:])
    out = {}
    for p in parts:
        if ":" not in p: continue
        k, v = p.split(":", 1)
        key, v = k.strip(), v.strip()
        if v.startswith("0x"):
            try: out[key] = int(v, 16)
            except: out[key] = v
        elif len(v) >= 2 and v[0] == "'" and v[-1] == "'":
            raw = v[1:-1]
            if key in ("ver","id","brd","mrkt","sid"): out[key] = hexstr_to_ascii(raw)
            elif key in ("mac","rmac"): out[key] = hex_to_mac(raw)
            else: out[key] = raw
        else:
            # fallback (ak by niečo prišlo ako plain číslo/true/false)
            try: out[key] = int(v)
            except: out[key] = v
    # derived
    if isinstance(out.get("ip"), int):  out["ip_str"]  = hex_to_ip_le(out["ip"])
    if isinstance(out.get("cip"), int): out["cip_str"] = hex_to_ip_le(out["cip"])
    if isinstance(out.get("temp"), int): out["temp_c"] = out["temp"]
    if isinstance(out.get("upt"), int):  out["uptime_seconds"] = out["upt"]
    return out

def fetch(host, user, pwd, ep):
    url = f"http://{host}/{ep}"
    r = requests.get(url, auth=HTTPDigestAuth(user, pwd), timeout=10)
    return r.status_code, r.text

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True)
    ap.add_argument("--user", default="admin")
    ap.add_argument("--password", required=True)
    args = ap.parse_args()

    for ep in ["sys.b","link.b","stats.b"]:
        code, body = fetch(args.host, args.user, args.password, ep)
        print(f"\n=== {ep} status {code} ===")
        if code == 200 and body.strip().startswith("{"):
            parsed = parse_swos_blob(body)
            print("keys:", ", ".join(sorted(parsed.keys())))
            print(json.dumps(parsed, indent=2))
        else:
            print(body[:200].replace("\n"," "))

if __name__ == "__main__":
    main()
