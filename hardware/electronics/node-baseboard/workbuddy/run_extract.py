#!/usr/bin/env python3
"""Chunked pin extraction: call bridge in batches to avoid the 500 on large loops."""
import json, subprocess, sys

TEMPLATE = r'''
const comps = await eda.sch_PrimitiveComponent.getAll();
const out = {};
let n = 0, idx = 0;
const OFFSET = __OFFSET__, LIMIT = __LIMIT__;
for (const c of comps){
  if (c.componentType !== "part") continue;
  if (idx < OFFSET){ idx++; continue; }
  if (n >= LIMIT) break;
  const pid = c.primitiveId;
  let pins = [];
  try { pins = await eda.sch_PrimitiveComponent.getAllPinsByPrimitiveId(pid); }
  catch(e){ pins = [{err: String(e)}]; }
  out[pid] = {
    x: c.x, y: c.y, rotation: c.rotation,
    name: c.component ? c.component.name : null,
    designator: c.designator, lcsc: c.supplierId,
    pins: pins.map(p => ({n: String(p.pinNumber), name: String(p.pinName), lx: p.x, ly: p.y}))
  };
  n++; idx++;
}
out.__count = n;
return out;
'''

def call(code, timeout=90):
    r = subprocess.run([sys.executable, "eda_bridge.py", code, "--timeout", str(timeout)],
                       capture_output=True, text=True)
    txt = r.stdout.strip()
    try:
        return json.loads(txt)
    except Exception:
        return {"__raw__": txt[:200]}

merged = {}
OFFSET = 0
LIMIT = 15
while True:
    code = TEMPLATE.replace("__OFFSET__", str(OFFSET)).replace("__LIMIT__", str(LIMIT))
    d = call(code)
    if "__error__" in d:
        print(f"[batch @{OFFSET}] ERROR: {d['__error__']}")
        # retry once
        d = call(code)
        if "__error__" in d:
            print(f"[batch @{OFFSET}] FAILED AGAIN, stopping"); break
    res = d.get("result", d)
    cnt = res.pop("__count", 0)
    for k, v in res.items():
        merged[k] = v
    print(f"[batch @{OFFSET}] got {cnt} parts, total {len(merged)}")
    if cnt < LIMIT:
        break
    OFFSET += LIMIT

json.dump(merged, open("pins_raw.json", "w"), ensure_ascii=False, indent=1)
print("WROTE pins_raw.json with", len(merged), "parts")
