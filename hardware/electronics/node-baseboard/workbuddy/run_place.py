#!/usr/bin/env python3
# Chunked placement driver. Places manifest.json components via Bridge in batches
# of CHUNK, verifying count after each batch to avoid the async-backlog problem.
import json, subprocess, sys, time

LIB = "0819f05c4eef4c71ace90d822a990e87"
CHUNK = 12
m = json.load(open("manifest.json", encoding="utf-8"))
items = [{"id": p["id"], "dev": p["dev"], "x": p["x"], "y": p["y"], "rot": p["rot"]} for p in m]


def bridge(code, timeout=90):
    import tempfile, os
    fd, path = tempfile.mkstemp(suffix=".js", dir=".")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(code)
        p = subprocess.run(
            ["python", "eda_bridge.py", "--file", path, "--timeout", str(timeout)],
            capture_output=True, text=True, cwd=".")
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
    out = p.stdout.strip()
    try:
        raw = json.loads(out)
    except Exception:
        return {"__error__": "bad-json", "raw": out[:300]}
    if not raw.get("success"):
        return raw
    return raw["result"]


def count_parts():
    r = bridge("var c=await eda.sch_PrimitiveComponent.getAll();"
               "return c.filter(x=>x.componentType==='part').length;", timeout=30)
    return r if isinstance(r, int) else -1


def place_chunk(chunk):
    code = f"""
const LIB="{LIB}";
const items = {json.dumps(chunk, ensure_ascii=False)};
const out = [];
for (const it of items) {{
  try {{
    const r = await eda.sch_PrimitiveComponent.create({{libraryUuid:LIB, uuid: it.dev}}, it.x, it.y, "", it.rot, false, true, true);
    out.push({{id: it.id, pid: r.primitiveId, ok:true}});
  }} catch(e) {{ out.push({{id: it.id, ok:false, err:String(e)}}); }}
}}
return JSON.stringify(out);
"""
    res = bridge(code, timeout=90)
    if isinstance(res, str):
        try:
            return json.loads(res)
        except Exception:
            return {"__error__": "bad-result", "raw": res[:300]}
    return res


placement = {}
failures = []
before = count_parts()
print(f"starting parts count = {before}")

for i in range(0, len(items), CHUNK):
    chunk = items[i:i+CHUNK]
    res = place_chunk(chunk)
    if isinstance(res, list):
        for r in res:
            if r.get("ok"):
                placement[r["id"]] = r["pid"]
            else:
                failures.append((r["id"], r.get("err")))
        ok = sum(1 for r in res if r.get("ok"))
        print(f"chunk {i//CHUNK}: placed {ok}/{len(chunk)}  total={len(placement)}")
    else:
        print(f"chunk {i//CHUNK}: ERROR {res}")
        for it in chunk:
            failures.append((it["id"], "chunk-error"))
    time.sleep(0.5)

# final stabilization: count should equal len(placement)
time.sleep(1)
after = count_parts()
print(f"final parts count = {after}  mapped = {len(placement)}")
if after != len(placement):
    print(f"WARNING: count mismatch (possible async backlog). mapped={len(placement)} actual={after}")

json.dump(placement, open("placement.json", "w", encoding="utf-8"), indent=2)
if failures:
    print("FAILURES:")
    for fid, err in failures:
        print("  ", fid, err)
else:
    print("ALL PLACED OK")
