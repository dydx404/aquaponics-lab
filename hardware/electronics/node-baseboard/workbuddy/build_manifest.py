#!/usr/bin/env python3
# Generate component placement manifest for node-baseboard v0.1.
# Each instance: id, type (key into type_uuids.json), value, module, x, y, rot.
# Coordinates in 0.01 inch (EasyEDA schematic unit). Modules laid on a grid.
import json

TYPES = json.load(open("type_uuids.json", encoding="utf-8"))

PX, PY = 560, 480          # module-internal pitch
GX, GY = 4600, 3200        # module spacing (between module anchors)

parts = []  # (id, type, value, module, col, row, rot)

def add(id, type, value, module, col, row, rot=0):
    parts.append((id, type, value, module, col, row, rot))

# ---- Module anchors (top-left of each module bounding box) ----
# x grows right, y grows DOWN (EasyEDA screen coords)
anchors = {
    "PWR":     (0,     0),
    "DEVKIT":  (0,     4200),
    "I2C":     (7000,  0),
    "ONEW":    (7000,  1600),
    "DIN":     (9000,  0),
    "MOS":     (9000,  4200),
    "SERVO":   (15000, 0),
    "WS":      (15000, 1600),
    "PZEM":    (15000, 2600),
    "INA":     (21000, 0),
    "ADS":     (21000, 1800),
    "MCP":     (21000, 3600),
    "PROBE":   (27000, 0),
    "PUMP":    (27000, 2200),
    "HW":      (33000, 0),
    "BME":     (33000, 1600),
    "PWRIN":   (0,     8400),
}

# ===== §2.1 12V input protection =====
add("F1",   "F1",     "5A",        "PWR", 0, 0)
add("Q1",   "Q1",     "AO4407A",   "PWR", 1, 0)
add("R1",   "R10k",   "10k",       "PWR", 2, 0)
add("R2",   "R100k",  "100k",      "PWR", 3, 0)
add("D1",   "D1",     "SMBJ15A",    "PWR", 4, 0)
add("D2",   "D2",     "1N4744A",    "PWR", 5, 0)

# ===== §2.2 Buck 12V->5V =====
add("U1",   "U1",     "MP1584EN",  "PWR", 0, 1)
add("L1",   "L1",     "47uH",      "PWR", 1, 1)
add("C1",   "C10u",   "10uF",      "PWR", 2, 1)
add("C2",   "C220u",  "220uF",     "PWR", 3, 1)
add("C3",   "C22u",   "22uF",      "PWR", 4, 1)
add("C4",   "C220u",  "220uF",     "PWR", 5, 1)
add("R3",   "R68k",   "68k",       "PWR", 0, 2)
add("R4",   "R13k",   "13k",       "PWR", 1, 2)
add("C5",   "C100n",  "100nF",     "PWR", 2, 2)

# ===== §2.3 LDO 5V->3.3V =====
add("U2",   "U2",     "AMS1117-3.3","PWR", 0, 3)
add("C6",   "C10u",   "10uF",      "PWR", 1, 3)
add("C7",   "C10u",   "10uF",      "PWR", 2, 3)
add("D3",   "LEDg",   "LED",       "PWR", 3, 3)
add("R5",   "R1k",    "1k",        "PWR", 4, 3)

# ===== §3 DevKitC socket (single 38-pin 2x19) =====
add("J_DEV","HDR19",  "DevKitC",   "DEVKIT", 0, 0)

# ===== §4 I2C =====
add("R6",   "R4k7",   "4.7k",      "I2C", 0, 0)
add("R7",   "R4k7",   "4.7k",      "I2C", 1, 0)
add("J_I2C","JST4",   "I2C",       "I2C", 2, 0)

# ===== §5 1-Wire =====
add("R8",   "R4k7",   "4.7k",      "ONEW", 0, 0)
add("J_1W", "JST3",   "1-Wire",    "ONEW", 1, 0)

# ===== §6 Digital inputs (6 ch) =====
# channel c=0..5 : R_pull, R_series, C_filter, D_clamp stacked; J_DIN below
for c in range(6):
    base = 100 + c  # designator base for this channel
    add(f"R_pull{c+1}", "R10k",  "10k",   "DIN", c, 0)
    add(f"R_ser{c+1}",  "R1k",   "1k",    "DIN", c, 1)
    add(f"C_flt{c+1}",  "C100n", "100nF", "DIN", c, 2)
    add(f"D_cl{c+1}",   "Dclamp","BAT54S","DIN", c, 3)
# level-shift MOSFETs for CH2/CH3 (5V pulse)
add("Q_lvl1", "Qlvl",  "BSS138",   "DIN", 6, 0)
add("Q_lvl2", "Qlvl",  "BSS138",   "DIN", 7, 0)
add("R_p5V1", "R10k",  "10k",      "DIN", 6, 1)
add("R_p5V2", "R10k",  "10k",      "DIN", 7, 1)
# terminal blocks
for c in range(6):
    add(f"J_DIN{c+1}", "TERM2", "DIN", "DIN", c, 5)

# ===== §7 MOSFET outputs (4 ch) =====
for c in range(4):
    add(f"Q_mos{c+1}", "Qmos",  "IRLZ44N", "MOS", c, 0)
    add(f"D_fly{c+1}", "Dfly",  "1N5819",  "MOS", c, 1)
    add(f"R_gate{c+1}","R100",  "100",     "MOS", c, 2)
    add(f"R_pd{c+1}",  "R10k",  "10k",     "MOS", c, 3)
    add(f"D_mos{c+1}", "LEDr",  "LED",     "MOS", c, 4)
    add(f"R_mled{c+1}","R1k",   "1k",      "MOS", c, 5)
    add(f"J_MOS{c+1}", "TERM2", "MOS",     "MOS", c, 6)

# ===== §8 Servo =====
add("J_SV1", "HDR3",  "SV1",  "SERVO", 0, 0)
add("J_SV2", "HDR3",  "SV2",  "SERVO", 1, 0)
add("R_sv1", "R1k",   "1k",   "SERVO", 0, 1)
add("R_sv2", "R1k",   "1k",   "SERVO", 1, 1)

# ===== §9 WS2812 =====
add("Q_ws",  "Qlvl",  "BSS138", "WS", 0, 0)
add("R_ws1", "R100",  "100",    "WS", 1, 0)
add("R_ws2", "R4k7",  "4.7k",   "WS", 2, 0)
add("J_WS",  "HDR3",  "WS2812", "WS", 3, 0)

# ===== §10 PZEM UART =====
add("Q_tx",   "Qlvl",  "BSS138", "PZEM", 0, 0)
add("Q_rx",   "Qlvl",  "BSS138", "PZEM", 1, 0)
add("R_tx33", "R10k",  "10k",    "PZEM", 0, 1)
add("R_tx5",  "R10k",  "10k",    "PZEM", 0, 2)
add("R_rx33", "R10k",  "10k",    "PZEM", 1, 1)
add("R_rx5",  "R10k",  "10k",    "PZEM", 1, 2)
add("J_PZEM", "HDR4",  "PZEM",   "PZEM", 2, 0)

# ===== §11 INA226 =====
add("U_INA",  "UINA",  "INA226", "INA", 0, 0)
add("R_shunt","Rshunt","0.01R",  "INA", 1, 0)
add("C_ina",  "C100n", "100nF",  "INA", 2, 0)

# ===== §12 ADS1115 + 3 probe inputs =====
add("U_ADS",  "UADS",  "ADS1115","ADS", 0, 0)
add("C_ads",  "C100n", "100nF",  "ADS", 1, 0)
add("J_ADS0", "TERM2", "pH",     "ADS", 0, 1)
add("J_ADS1", "TERM2", "EC/TDS", "ADS", 1, 1)
add("J_ADS2", "TERM2", "Turb",   "ADS", 2, 1)

# ===== §13 MCP23017 =====
add("U_MCP",  "UMCP",  "MCP23017","MCP", 0, 0)
add("C_mcp",  "C100n", "100nF",  "MCP", 1, 0)

# ===== §12.1 Probe supply (3 ch) =====
for c in range(3):
    add(f"Q_prb{c+1}",  "Qprobe","SI2302", "PROBE", c, 0)
    add(f"R_ppd{c+1}",  "R10k",  "10k",    "PROBE", c, 1)
add("J_PRB", "HDR6",  "PRB",   "PROBE", 0, 2)

# ===== §14 Pump control =====
add("U_OPTO", "Uopto", "PC817",  "PUMP", 0, 0)
add("R_led",  "R330",  "330",    "PUMP", 1, 0)
add("R_pl",   "R10k",  "10k",    "PUMP", 2, 0)
add("R_pdpm", "R10k",  "10k",    "PUMP", 3, 0)
add("JP_VCC", "HDR3",  "VCC_SEL","PUMP", 4, 0)
add("JP_NCNO","HDR3",  "NO/NC",  "PUMP", 5, 0)
add("J_PUMP", "TERM3", "PUMP",   "PUMP", 6, 0)

# ===== §15 High water float =====
add("U_OPTO2","Uopto", "PC817",  "HW", 0, 0)
add("R_hw",   "R1k",   "1k",     "HW", 1, 0)
add("J_HW",   "TERM2", "HW_FLOAT","HW", 2, 0)

# ===== §16 BME280 =====
add("U_BME",  "UBME",  "BME280", "BME", 0, 0)
add("C_bme",  "C100n", "100nF",  "BME", 1, 0)

# ===== §17 J_12V input =====
add("J_12V",  "TERM2", "12V_IN", "PWRIN", 0, 0)

# ---- compute absolute coordinates ----
manifest = []
for (id, type, value, module, col, row, rot) in parts:
    ax, ay = anchors[module]
    x = ax + col * PX
    y = ay + row * PY
    manifest.append({
        "id": id, "type": type, "value": value, "module": module,
        "x": x, "y": y, "rot": rot,
        "dev": TYPES[type]["dev"], "sym": TYPES[type]["sym"],
        "lcsc": TYPES[type]["lcsc"]
    })

json.dump(manifest, open("manifest.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(f"Total instances: {len(manifest)}")
by_mod = {}
for m in manifest:
    by_mod.setdefault(m["module"], 0)
    by_mod[m["module"]] += 1
for k, v in by_mod.items():
    print(f"  {k:7s} {v}")
# bounding box check
xs = [m["x"] for m in manifest]; ys = [m["y"] for m in manifest]
print(f"X range {min(xs)}..{max(xs)}  Y range {min(ys)}..{max(ys)}")
