#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Authoritative netlist rebuild for node-baseboard v0.1.

Maps DESIGN.md (PR #5) + PIN-MAPPING.md onto the ACTUALLY PLACED components'
real symbol pin names (pins.json). Replaces the flawed nets.json AND the
first-pass nets2.py (which had: a 12V-5V short, missing buck support
network, shorted BSS138 level shifters, floating MOSFET status-LED anodes,
floating I2C address pins, and DevKitC 3V3 pins wrongly tied against R-1).

Pin-name conventions (verified from pins.json live extract):
  Passives R/C/L: '1','2'
  R_shunt (Kelvin 4T): 'I1','I2' (current path) 'E1','E2' (sense)
  Diodes SMBJ15A/1N4744A/1N5819: 'A','K'
  LEDs KT-0805x / LED: 'A'(anode),'K'(cathode)
  N-MOS/P-MOS/BSS138/SI2302: 'D','G','S'
  PC817: 'A'(anode),'C'(cathode),'EM'(emitter),'COL'(collector)
  BAT54S clamp: '1','2','3'  (1=signal, 2=GND, 3=3V3)
  ICs: real names (INA226/ADS1115/MCP23017/MP1584/AMS1117/BME280)
  J_DEV HDR19(38p): Lk->pin(2k-1) left col, Rk->pin(2k) right col
  Connectors (KF128/JST/HDR): pin NUMBER as name
"""
import json

pins = json.load(open("pins.json"))

# ---------- resolution helpers ----------
def P(cid, pin, note=""):
    return [cid, pin, note]

def jdev(ref):
    k = int(ref[1:])
    return str(2*k-1) if ref[0] in "Ll" else str(2*k)

def verify(netdict):
    errors = []
    for net, eps in netdict.items():
        for cid, pin, note in eps:
            d = pins.get(cid)
            if not d:
                errors.append(f"{net}: no component {cid}")
                continue
            names = {p["name"] for p in d["pins"]}
            if pin not in names:
                errors.append(f"{net}: {cid} has no pin '{pin}' (avail={sorted(names)})")
    return errors

def coverage(netdict):
    used = set()
    for eps in netdict.values():
        for cid, pin, note in eps:
            used.add(cid)
    allc = set(pins.keys())
    return sorted(allc - used)

# GPIO -> J_DEV pin (verified against DESIGN §3.2)
#   CH1=GPIO13(L16) CH2=GPIO34(R12) CH3=GPIO35(R11) CH4=GPIO36(R14)
#   CH5=GPIO39(R13) CH6=GPIO32(R10)
DIN_GPIO = {1: jdev("L16"), 2: jdev("R12"), 3: jdev("R11"),
            4: jdev("R14"), 5: jdev("R13"), 6: jdev("R10")}
# MOSFET outputs: CH1=GPIO33(R9) CH2=GPIO14(R5) CH3=GPIO18(L9) CH4=GPIO19(R10)
MOS_GPIO = {1: jdev("R9"), 2: jdev("R5"), 3: jdev("L9"), 4: jdev("R10")}
# Servo: SV1=GPIO25(R8) SV2=GPIO26(R7)
SV_GPIO = {1: jdev("R8"), 2: jdev("R7")}

N = {}

# =================== POWER ===================
# 12V_IN: source + -> fuse in
N["12V_IN"] = [P("J_12V","1","+12V source +"), P("F1","1","fuse in")]

# 12V_BUS = post-protection, PRE-shunt tap (DESIGN §2.1 + §11 "分流前")
N["12V_BUS"] = [
    P("F1","2","fuse out"),
    P("Q1","D","P-MOS drain = input side"),
    P("D1","K","TVS cathode (anode->GND)"),
    P("U1","VIN","buck input"),
    P("C1","1","buck input cap"),
    P("C2","1","buck input bulk cap"),
    P("U1","EN","buck enable (tied to 12V = on)"),
    P("U_INA","VBUS","INA226 bus voltage monitor"),
    P("U_INA","VIN+","shunt high side (分流前)"),
    P("R_shunt","I1","shunt current terminal (high side)"),
]

# 12V_LOAD = POST-shunt 12V that feeds the switched 12V loads (DESIGN §11 "分流后")
N["12V_LOAD"] = [
    P("U_INA","VIN-","shunt low side (分流后)"),
    P("R_shunt","I2","shunt current terminal (low side)"),
    P("J_MOS1","1","+12V to load terminal"),
    P("J_MOS2","1","+12V to load terminal"),
    P("J_MOS3","1","+12V to load terminal"),
    P("J_MOS4","1","+12V to load terminal"),
    # MOSFET status-LED anodes are fed from 12V_LOAD through R_mled
    P("R_mled1","1","LED limit from 12V_LOAD"),
    P("R_mled2","1","LED limit from 12V_LOAD"),
    P("R_mled3","1","LED limit from 12V_LOAD"),
    P("R_mled4","1","LED limit from 12V_LOAD"),
]

# SW = MP1584 switch node (DESIGN §2.2). BST-C5-SW are connected through C5.
N["SW"] = [
    P("U1","SW","switch node"),
    P("L1","1","inductor -> 5V output"),
    P("C5","2","bootstrap cap -> BST"),
    P("U1","BST","bootstrap"),
    P("C5","1","bootstrap cap other end"),
]

# 5V = buck output rail (DESIGN §2.2 / §2.4)
N["5V"] = [
    P("L1","2","inductor output = 5V"),
    P("C3","1","buck output cap"),
    P("C4","1","buck output bulk cap"),
    P("U2","VIN","LDO input = 5V"),
    P("C6","1","LDO input cap (5V)"),
    P("J_DEV", jdev("L18"), "DevKitC VIN(5V)"),
    P("J_DEV", jdev("R1"), "DevKitC VIN(5V) parallel"),
    # 5V device supply (servo/WS2812/PZEM/level-shift 5V side)
    P("J_SV1","1"), P("J_SV2","1"), P("J_WS","1"), P("J_PZEM","1"),
    # 5V pullups for level shifters
    P("R_p5V1","1","CH2 5V pullup"), P("R_p5V2","1","CH3 5V pullup"),
    P("R_ws2","1","WS 5V data pullup"),
    P("R_tx5","1","PZEM TX 5V pullup"), P("R_rx5","1","PZEM RX 5V pullup"),
]

# 3V3 = LDO output (sensing rail) -- DevKitC 3V3 pins are NC per R-1 (DESIGN §2.3)
N["3V3"] = [
    P("U2","VOUT","LDO 3.3V out"),
    P("U2","VOUT","LDO 3.3V out (dup pad)"),
    P("C7","1","LDO output cap"),
    P("R5","1","pwr LED limit from 3V3"),
    P("R6","1","SDA pullup"), P("R7","1","SCL pullup"), P("R8","1","1-Wire pullup"),
    # DIN 3.3V pullups (dry-contact channels 1,4,5,6; and 3.3V side of CH2/3)
    P("R_pull1","1"), P("R_pull2","1"), P("R_pull3","1"),
    P("R_pull4","1"), P("R_pull5","1"), P("R_pull6","1"),
    P("U_INA","VS+","INA226 analog supply"),
    P("U_ADS","VDD","ADS1115 VDD"),
    P("U_MCP","VDD","MCP23017 VDD"),
    P("U_BME","VDD","BME280 VDD"),
    P("U_BME","VDDIO","BME280 VDDIO"),
    P("U_BME","CSB","BME280 CSB=HIGH for I2C mode"),
    P("J_I2C","1","I2C 3.3V"),
    P("J_1W","1","1-Wire 3.3V"),
    # BSS138 gate tie to 3.3V (level shifters)
    P("Q_lvl1","G","CH2 BSS138 gate->3.3V"),
    P("Q_lvl2","G","CH3 BSS138 gate->3.3V"),
    P("Q_ws","G","WS BSS138 gate->3.3V"),
    P("Q_tx","G","PZEM-TX BSS138 gate->3.3V"),
    P("Q_rx","G","PZEM-RX BSS138 gate->3.3V"),
    # 3.3V pullups for PZEM level shifters
    P("R_tx33","1","PZEM TX 3.3V pullup"),
    P("R_rx33","1","PZEM RX 3.3V pullup"),
    # BAT54S clamp top -> 3V3 (all 6 channels)
    P("D_cl1","3"), P("D_cl2","3"), P("D_cl3","3"),
    P("D_cl4","3"), P("D_cl5","3"), P("D_cl6","3"),
    # JP_VCC selectable rail (3.3V side of the 3-pin VCC_SEL header)
    P("JP_VCC","1","VCC_SEL 3.3V option"),
]

# GND (DESIGN §2.x). Opto emitters are ISOLATED (GND_ISO), NOT here.
N["GND"] = [
    P("J_12V","2","GND return"),
    P("Q1","S","P-MOS source = load/GND side"),
    P("D1","A","TVS anode"),
    P("R1","2","Q1 gate pulldown to GND"),
    P("D2","K","zener cathode to GND (anode->gate)"),
    P("U1","GND","buck GND"),
    P("U1","GND","buck GND (dup pad)"),
    P("C1","2","in cap"), P("C2","2","bulk"), P("C3","2","out"), P("C4","2","bulk"),
    P("C6","2","LDO in cap"), P("C7","2","LDO out cap"),
    P("U2","GND","LDO GND"),
    P("D3","K","pwr LED cathode"),
    # DevKitC GND pins (DESIGN §3.2: left2,left17,right2,right18)
    P("J_DEV", jdev("L2"), "DevKitC GND"),
    P("J_DEV", jdev("L17"), "DevKitC GND"),
    P("J_DEV", jdev("R2"), "DevKitC GND"),
    P("J_DEV", jdev("R18"), "DevKitC GND"),
    # DIN: terminal GND, filter cap GND, clamp GND pin
    P("C_flt1","2"), P("C_flt2","2"), P("C_flt3","2"),
    P("C_flt4","2"), P("C_flt5","2"), P("C_flt6","2"),
    P("J_DIN1","2"), P("J_DIN2","2"), P("J_DIN3","2"),
    P("J_DIN4","2"), P("J_DIN5","2"), P("J_DIN6","2"),
    P("D_cl1","2"), P("D_cl2","2"), P("D_cl3","2"),
    P("D_cl4","2"), P("D_cl5","2"), P("D_cl6","2"),
    # MOSFETs: source->GND, flyback cathode->GND, gate pulldown->GND, LED cathode->GND
    P("Q_mos1","S"), P("Q_mos2","S"), P("Q_mos3","S"), P("Q_mos4","S"),
    P("D_fly1","K"), P("D_fly2","K"), P("D_fly3","K"), P("D_fly4","K"),
    P("R_pd1","2"), P("R_pd2","2"), P("R_pd3","2"), P("R_pd4","2"),
    P("D_mos1","K"), P("D_mos2","K"), P("D_mos3","K"), P("D_mos4","K"),
    # servo/WS/PZEM/I2C/1W GND
    P("J_SV1","2"), P("J_SV2","2"), P("J_WS","2"),
    P("J_PZEM","2"), P("J_I2C","2"), P("J_1W","2"),
    # ICs
    P("U_INA","GND"), P("U_ADS","GND"), P("U_MCP","VSS"),
    P("U_BME","GND"),
    P("C_ina","2"), P("C_ads","2"), P("C_mcp","2"), P("C_bme","2"),
    # I2C address pins -> GND (DESIGN §4: INA226 A0/A1, ADS ADDR, MCP A0/A1/A2)
    P("U_INA","A0"), P("U_INA","A1"),
    P("U_ADS","ADDR"),
    P("U_MCP","A0"), P("U_MCP","A1"), P("U_MCP","A2"),
    # BME280 SDO->GND for address 0x76 (DESIGN §16)
    P("U_BME","SDO"),
    # ADS A3 spare tied to GND (clean ERC)
    P("U_ADS","AIN3"),
    # pump LED cathode side + GPIO27 pulldown
    P("U_OPTO","C","PC817 LED cathode -> GND"),
    P("R_pdpm","2","GPIO27 pulldown to GND"),
    # R2 (100k) gate-source resistor of Q1 -> source(=GND)
    P("R2","2","Q1 gate-source resistor (other->gate)"),
    # probe switches source->GND, gate pulldown->GND
    P("Q_prb1","S"), P("Q_prb2","S"), P("Q_prb3","S"),
    P("R_ppd1","2"), P("R_ppd2","2"), P("R_ppd3","2"),
    # probe header GND pins
    P("J_PRB","2"), P("J_PRB","4"), P("J_PRB","6"),
    # high-water float COM->GND (NC closed by default)
    P("J_HW","2","FLOAT_COM -> GND"),
    # opto2 LED cathode -> GND (HW float return)
    P("U_OPTO2","C","PC817-2 LED cathode -> GND"),
    # ADS BNC GND
    P("J_ADS0","2"), P("J_ADS1","2"), P("J_ADS2","2"),
]

# =================== I2C ===================
N["SDA"] = [P("U_INA","SDA"), P("U_ADS","SDA"), P("U_MCP","SDA"),
            P("U_BME","SDI","BME280 I2C data (SPI-symbol note)"),
            P("J_I2C","3","SDA to external"),
            P("J_DEV", jdev("L11"), "GPIO21 SDA"),
            P("R6","2","pullup")]
N["SCL"] = [P("U_INA","SCL"), P("U_ADS","SCL"), P("U_MCP","SCK","MCP23017 I2C clk = SCK"),
            P("U_BME","SCK","BME280 I2C clk (SPI-symbol note)"),
            P("J_I2C","4","SCL to external"),
            P("J_DEV", jdev("L14"), "GPIO22 SCL"),
            P("R7","2","pullup")]

# =================== 1-Wire ===================
N["1WIRE"] = [P("J_1W","3","DATA"),
              P("J_DEV", jdev("L5"), "GPIO4 1-Wire"),
              P("R8","2","pullup")]

# =================== DIGITAL INPUTS ===================
# Dry-contact channels (CH1,4,5,6): 3.3V pullup + series + filter + clamp + GPIO
for i in (1, 4, 5, 6):
    N[f"DIN{i}"] = [
        P(f"J_DIN{i}","1","terminal signal (dry contact to GND)"),
        P(f"R_pull{i}","1","pullup -> 3V3 (other end)"),
        P(f"R_ser{i}","1","series R"),
        P(f"C_flt{i}","1","filter cap other end->GND"),
        P(f"D_cl{i}","1","clamp signal pin"),
        P(f"R_ser{i}","2", f"GPIO for CH{i}"),
        P("J_DEV", DIN_GPIO[i], f"GPIO for CH{i}"),
    ]

# 5V pulse channels (CH2,CH3): BSS138 level shift (DESIGN §6.2)
#   5V side:  J_DIN.x.1 -> Q_lvl.D -> R_p5V.x (pullup to 5V)
#   3.3V side: Q_lvl.S -> R_ser -> GPIO ; R_pull (3.3V) + C_flt + D_cl
for i, qlvl in ((2, "Q_lvl1"), (3, "Q_lvl2")):
    N[f"DIN{i}_5V"] = [
        P(f"J_DIN{i}","1","5V sensor signal"),
        P(qlvl,"D","BSS138 drain (5V side)"),
        P(f"R_p5V{i-1}","1","5V pullup (other->5V)"),
    ]
    N[f"DIN{i}_3V3"] = [
        P(qlvl,"S","BSS138 source (3.3V side)"),
        P(f"R_ser{i}","1","series R"),
        P(f"R_pull{i}","1","3.3V pullup (other->3V3)"),
        P(f"C_flt{i}","1","filter cap other end->GND"),
        P(f"D_cl{i}","1","clamp signal pin"),
        P(f"R_ser{i}","2", f"GPIO for CH{i}"),
        P("J_DEV", DIN_GPIO[i], f"GPIO for CH{i}"),
    ]

# =================== MOSFET OUTPUTS (4x low-side) ===================
for i in range(1, 5):
    g = MOS_GPIO[i]
    N[f"MOS{i}_GATE"] = [
        P(f"Q_mos{i}","G","gate"),
        P(f"R_gate{i}","2","gate series R (other->GPIO)"),
        P(f"R_pd{i}","1","gate pulldown (other->GND)"),
        P("J_DEV", g, f"GPIO MOS{i}"),
        P(f"R_gate{i}","1","to GPIO (same as J_DEV endpoint)"),
    ]
    N[f"MOS{i}_DRAIN"] = [
        P(f"Q_mos{i}","D","drain"),
        P(f"D_fly{i}","A","flyback anode (cathode->GND)"),
        P(f"D_mos{i}","A","status LED anode (cathode->drain)"),
        P(f"D_mos{i}","K","status LED cathode"),
        P(f"J_MOS{i}","2","load- terminal"),
        P(f"R_mled{i}","2","LED limit (other->12V_LOAD)"),
    ]

# =================== SERVO PWM ===================
for i in (1, 2):
    N[f"SV{i}"] = [P(f"J_SV{i}","3","PWM"),
                   P(f"R_sv{i}","2","signal limit (other->GPIO)"),
                   P("J_DEV", SV_GPIO[i], f"GPIO servo{i}"),
                   P(f"R_sv{i}","1","to GPIO")]

# =================== WS2812 (BSS138 3.3V->5V) ===================
N["WS_3V3"] = [
    P("J_DEV", jdev("L15"), "GPIO23 WS data"),
    P("R_ws1","1","series R (GPIO side)"),
    P("R_ws1","2","series R (source side)"),
    P("Q_ws","S","level-shift source (3.3V GPIO side)"),
]
N["WS_5V"] = [
    P("J_WS","3","DATA"),
    P("Q_ws","D","drain -> 5V data"),
    P("R_ws2","1","5V data pullup (other->5V)"),
]

# =================== PZEM UART (2x BSS138) ===================
# TX: ESP32 GPIO17(L7) -> Q_tx -> PZEM RX (J_PZEM pin4)
N["PZEM_TX_3V3"] = [
    P("J_DEV", jdev("L7"), "GPIO17 TX"),
    P("Q_tx","S","3.3V side"),
    P("R_tx33","2","3.3V pullup (other->3.3V)"),
]
N["PZEM_TX_5V"] = [
    P("Q_tx","D","5V side"),
    P("R_tx5","1","5V pullup (other->5V)"),
    P("J_PZEM","4","PZEM RX"),
]
# RX: PZEM TX (J_PZEM pin3) -> Q_rx -> ESP32 GPIO16(L6)
N["PZEM_RX_5V"] = [
    P("J_PZEM","3","PZEM TX"),
    P("Q_rx","D","5V side"),
    P("R_rx5","1","5V pullup (other->5V)"),
]
N["PZEM_RX_3V3"] = [
    P("Q_rx","S","3.3V side"),
    P("R_rx33","2","3.3V pullup (other->3.3V)"),
    P("J_DEV", jdev("L6"), "GPIO16 RX"),
]

# =================== BUCK FEEDBACK (MP1584) ===================
# VOUT(5V) -> R3(68k) -> FB -> R4(13k) -> GND   (DESIGN §2.2)
N["FB"] = [
    P("U1","FB","feedback node"),
    P("R3","2","top of divider (other->5V)"),
    P("R4","1","bottom of divider (other->GND)"),
]

# =================== INA226 SENSE (Kelvin) ===================
# E1/E2 sense terminals tap VIN+/VIN- (already on 12V_BUS / 12V_LOAD)
# They are explicit here for clarity (same nets).
N["INA_SENSE_HI"] = [P("R_shunt","E1","sense + (shunt high side)"),
                     P("U_INA","VIN+","redundant tap")]
N["INA_SENSE_LO"] = [P("R_shunt","E2","sense - (shunt low side)"),
                     P("U_INA","VIN-","redundant tap")]

# =================== ADS1115 ANALOG INPUTS ===================
N["ADS_A0"] = [P("U_ADS","AIN0","pH"), P("J_ADS0","1","pH BNC")]
N["ADS_A1"] = [P("U_ADS","AIN1","TDS"), P("J_ADS1","1","TDS BNC")]
N["ADS_A2"] = [P("U_ADS","AIN2","turbidity"), P("J_ADS2","1","turbidity BNC")]

# =================== MCP23017 PROBE POWER CONTROL ===================
prb_map = {1: "GPA0", 2: "GPA1", 3: "GPA2"}
for i in (1, 2, 3):
    N[f"PRB{i}_CTL"] = [
        P("U_MCP", prb_map[i], f"GPA{i-1} -> Q_prb{i} gate"),
        P(f"Q_prb{i}","G","gate"),
        P(f"R_ppd{i}","1","gate pulldown (other->GND)"),
    ]
    vpin = str(2*i-1)
    N[f"PRB{i}_V"] = [
        P(f"Q_prb{i}","D","drain -> V_PROBE"),
        P("J_PRB", vpin, f"V_PROBE{i}"),
    ]

# =================== POWER LED (anode node) ===================
N["PWR_LED"] = [P("D3","A","LED anode"), P("R5","2","limit (other->3V3)")]

# =================== PUMP CONTROL (opto-isolated, active-high) ===================
# LED side: GPIO27 -> R_led -> U_OPTO.A ; cathode -> GND ; R_pdpm pulldown on GPIO27
N["PUMP_STOP"] = [
    P("J_DEV", jdev("R6"), "GPIO27 PUMP_STOP"),
    P("R_led","1","330R LED limit (other->GPIO)"),
    P("R_led","2","LED limit (other->anode)"),
    P("U_OPTO","A","PC817 LED anode (cathode->GND)"),
    P("R_pdpm","1","GPIO27 pulldown (other->GND)"),
]
# Isolated output side: VCC_SEL -> R_pl -> COL -> COM(J_PUMP.1)
N["PUMP_OUT"] = [
    P("JP_VCC","2","VCC_SEL COM (selected 3.3/5V)"),
    P("R_pl","1","output pullup (other->COM)"),
    P("U_OPTO","COL","PC817 collector"),
    P("J_PUMP","1","COM"),
]
# High-water opto2 cascaded in series on the isolated path
N["PUMP_CASCADE"] = [
    P("U_OPTO","EM","PC817 emitter -> opto2 collector"),
    P("U_OPTO2","COL","PC817-2 collector"),
]
# Isolated return (NOT board GND): opto2 emitter + NO contact (default)
N["GND_ISO"] = [
    P("U_OPTO2","EM","PC817-2 emitter -> isolated return"),
    P("J_PUMP","2","NO (default)"),
    P("JP_NCNO","1","NO jumper pin"),
    P("JP_NCNO","2","NO jumper common"),
]
# NC contact spare
N["PUMP_NC"] = [P("J_PUMP","3","NC (spare)"), P("JP_NCNO","3","NC jumper pin")]

# =================== HIGH-WATER FLOAT (independent safety, §15) ===================
# LED side: 12V -> R_hw -> U_OPTO2.A ; cathode -> J_HW.2 -> GND
N["HW_FLOAT"] = [
    P("J_HW","1","FLOAT_NC (+12V side)"),
    P("R_hw","2","1k limit (other->12V)"),
    P("U_OPTO2","A","PC817-2 LED anode (cathode->via R_hw from 12V)"),
]
# R_hw other end -> 12V (use 12V_BUS tap via a dedicated note; connect to 12V_BUS)
N["12V_BUS"].append(P("R_hw","1","HW float current limit from 12V"))

# =================== P-MOS GATE (Q1 reverse-protection gate drive, §2.1) ===================
# Q1.G pulled down to GND via R1(10k); D2 zener clamps Vgs; R2(100k) gate-source.
N["GATE_Q1"] = [
    P("Q1","G","P-MOS gate"),
    P("R1","1","gate pulldown (other->GND)"),
    P("D2","A","zener anode (cathode->GND)"),
    P("R2","1","gate-source resistor (other->GND via Q1.S)"),
]

# ---------- verify ----------
errs = verify(N)
json.dump(N, open("nets2.json", "w"), ensure_ascii=False, indent=1)
print(f"WROTE nets2.json: {len(N)} nets")
print(f"Total endpoints: {sum(len(v) for v in N.values())}")
if errs:
    print(f"\n!!! {len(errs)} RESOLUTION ERRORS:")
    for e in errs[:80]:
        print("  ", e)
else:
    print("ALL ENDPOINTS RESOLVED OK")
cov = coverage(N)
if cov:
    print(f"\n!!! {len(cov)} COMPONENTS NOT IN ANY NET (floating):")
    for c in cov:
        print("   ", c)
