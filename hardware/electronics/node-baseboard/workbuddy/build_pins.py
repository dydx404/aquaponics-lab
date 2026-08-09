#!/usr/bin/env python3
"""Merge pins_raw.json + placement.json + manifest.json -> pins.json (id-keyed, page coords)."""
import json

placement = json.load(open("placement.json"))   # id -> pid
manifest  = {m["id"]: m for m in json.load(open("manifest.json"))}
raw       = json.load(open("pins_raw.json"))      # pid -> {x,y,rotation,name,designator,lcsc,pins}

out = {}
rot_nonzero = []
for cid, pid in placement.items():
    r = raw.get(pid)
    if not r:
        print("WARN missing pid", pid, "for", cid); continue
    if r.get("rotation"):
        rot_nonzero.append((cid, r["rotation"]))
    pins = []
    for p in r["pins"]:
        pins.append({
            "n": p["n"], "name": p["name"],
            "lx": p["lx"], "ly": p["ly"],   # already page-level (API returns absolute)
        })
    m = manifest.get(cid, {})
    out[cid] = {
        "id": cid, "type": m.get("type"), "module": m.get("module"),
        "value": m.get("value"), "pid": pid,
        "designator": r.get("designator"), "lcsc": r.get("lcsc"),
        "name": r.get("name"),
        "rot": r.get("rotation", 0),
        "pins": pins,
    }

json.dump(out, open("pins.json", "w"), ensure_ascii=False, indent=1)
print("WROTE pins.json:", len(out), "components")
print("nonzero rotation parts:", rot_nonzero)
# quick sanity: pin counts per type
from collections import Counter
c = Counter(out[k]["type"] for k in out)
print("types:", dict(c))
