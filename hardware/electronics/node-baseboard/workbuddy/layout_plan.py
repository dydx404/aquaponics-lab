#!/usr/bin/env python3
"""node-baseboard 原理图按功能分区紧凑重排 -> 输出每个元件的平移 delta。

依据:
  pins.json    : cid -> {designator, pins:[{lx,ly}]}  (lx/ly 为相对元件原点的引脚偏移)
  pins_raw.json: pid -> {designator, x, y}            (x/y 为元件绝对原点, 散落布局)
输出:
  target_positions.json : cid -> {pid,designator,zone,cur_x,cur_y,target_x,target_y,dx,dy,w,h}
  (dx,dy 即 Bridge 平移 API 需施加的位移)
"""
import json

MARGIN = 80      # 元件本体四周留白(引脚之外的符号边距)
GAPX   = 120     # 同区元件水平间距
GAPY   = 180     # 同区元件垂直间距 / 区与区之间
BAND_W = 5200    # 每个功能区的可用宽度, 超出则换行
ORIGIN_X, ORIGIN_Y = 300, 300

# ---- 功能分区 (按 cid 前缀/关键字匹配) ----
ZONE_ORDER = ["POWER", "I2C", "IO", "MOSFET", "PROBE", "DEVKIT", "MISC"]

def zone_of(cid):
    c = cid
    if c in ("J_12V", "F1", "D1", "D2", "U1", "L1", "C1", "C2", "C3", "C4", "C5",
             "C6", "C7", "Q1", "R1", "R2", "R3", "R4", "R_p5V1", "R_p5V2",
             "JP_VCC", "JP_NCNO", "R_led", "R_pl"):
        return "POWER"
    if c in ("U_INA", "U_ADS", "U_MCP", "U_BME", "J_I2C", "J_1W", "C_ina",
             "C_ads", "C_mcp", "C_bme", "R5", "R6", "R7", "R8"):
        return "I2C"
    if (c.startswith(("J_DIN", "R_pull", "R_ser", "R_pd", "D_cl", "Q_lvl",
                      "Q_ws", "Q_tx", "Q_rx", "R_ws", "R_tx", "R_rx", "J_WS",
                      "J_PZEM", "J_SV", "R_sv"))):
        return "IO"
    if (c.startswith(("Q_mos", "D_fly", "D_mos", "R_gate", "R_mled", "J_MOS",
                      "J_PUMP", "U_OPTO"))):
        return "MOSFET"
    if (c.startswith(("J_PRB", "Q_prb", "R_ppd", "R_hw", "J_HW"))):
        return "PROBE"
    if c == "J_DEV":
        return "DEVKIT"
    return "MISC"

def main():
    pins = json.load(open("pins.json"))
    raw  = json.load(open("pins_raw.json"))

    # designator -> (x,y) 当前绝对原点
    raw_map = {}
    for v in raw.values():
        d = v.get("designator")
        if d:
            raw_map[d] = (v.get("x") or 0, v.get("y") or 0)

    # 计算每个元件占地尺寸 (相对坐标 spread + 边距); 收集到各分区
    comps = {}  # cid -> dict
    zones = {z: [] for z in ZONE_ORDER}
    for cid, d in pins.items():
        desig = d.get("designator")
        pxs = [p["lx"] for p in d["pins"]]
        pys = [p["ly"] for p in d["pins"]]
        w = (max(pxs) - min(pxs)) + 2 * MARGIN
        h = (max(pys) - min(pys)) + 2 * MARGIN
        cur = raw_map.get(desig, (None, None))
        z = zone_of(cid)
        rec = {"cid": cid, "designator": desig, "pid": d.get("pid"),
               "w": w, "h": h, "cur_x": cur[0], "cur_y": cur[1], "zone": z}
        comps[cid] = rec
        zones[z].append(rec)

    # 逐区排布: 每个区是一条水平带, 元件从左到右, 超出 BAND_W 换行
    target = {}
    cursor_y = ORIGIN_Y
    for z in ZONE_ORDER:
        items = zones[z]
        if not items:
            continue
        # 区标题留白
        cursor_x = ORIGIN_X
        row_h = 0
        zone_start_y = cursor_y
        items.sort(key=lambda r: (r["h"], r["w"]), reverse=True)
        for r in items:
            if cursor_x + r["w"] > ORIGIN_X + BAND_W:
                cursor_x = ORIGIN_X
                cursor_y += row_h + GAPY
                row_h = 0
            tx = cursor_x
            ty = cursor_y
            r["target_x"] = tx
            r["target_y"] = ty
            r["dx"] = (tx - r["cur_x"]) if r["cur_x"] is not None else None
            r["dy"] = (ty - r["cur_y"]) if r["cur_y"] is not None else None
            target[r["cid"]] = r
            cursor_x += r["w"] + GAPX
            row_h = max(row_h, r["h"])
        cursor_y += row_h + GAPY + 200  # 区与区间额外间距

    # 重叠自检
    overlaps = []
    boxes = [(r["target_x"], r["target_y"], r["target_x"] + r["w"],
              r["target_y"] + r["h"], r["designator"]) for r in target.values()]
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
            iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
            if ix > 0 and iy > 0:
                overlaps.append((a[4], b[4], ix, iy))
    # 缺失原点(无法平移)
    missing = [r["designator"] for r in target.values()
               if r["dx"] is None or r["dy"] is None]

    maxx = max(b[2] for b in boxes)
    maxy = max(b[3] for b in boxes)
    json.dump(target, open("target_positions.json", "w"), indent=1)

    # 报告
    print(f"components placed : {len(target)} / {len(pins)}")
    print(f"canvas extent     : {maxx} x {maxy}")
    print(f"overlaps          : {len(overlaps)}")
    for o in overlaps[:20]:
        print("   OVERLAP", o)
    print(f"missing origin    : {missing if missing else 'NONE'}")
    zc = {}
    for r in target.values():
        zc[r["zone"]] = zc.get(r["zone"], 0) + 1
    print("zone counts:", zc)
    print("WROTE target_positions.json")

if __name__ == "__main__":
    main()
