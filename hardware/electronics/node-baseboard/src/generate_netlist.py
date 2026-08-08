# SKiDL netlist generator for node-baseboard v0.1
#
# Prerequisites:
#   1. Install KiCad (provides symbol libraries)
#   2. pip install skidl
#   3. Set KICAD_SYMBOL_DIR env var to KiCad's symbol library folder
#      e.g. export KICAD_SYMBOL_DIR="/usr/share/kicad/symbols"
#   4. Run: python generate_netlist.py
#   5. Output: node-baseboard.net (KiCad netlist, importable into KiCad/嘉立创EDA)
#
# This script is the single source of truth for the circuit netlist.
# See DESIGN.md for detailed circuit descriptions and calculations.

from skidl import *
import os

# ── Configure library path ────────────────────────────────────────────
# Adjust this to your KiCad installation
KICAD_LIB = os.environ.get(
    "KICAD_SYMBOL_DIR",
    "/usr/share/kicad/symbols"  # Linux default; Windows: "C:/Program Files/KiCad/share/kicad/symbols"
)
lib_search_paths[KICAD] = [KICAD_LIB]

# ── Power nets ────────────────────────────────────────────────────────
v12 = Net("12V_BUS")    # 12V DC bus (after protection)
v5 = Net("+5V")         # 5V rail (from buck)
v33 = Net("+3V3")       # 3.3V rail (from LDO)
gnd = Net("GND")        # Common ground
gnd_iso = Net("GND_ISO") # Isolated ground for pump control

# ── Input Protection ──────────────────────────────────────────────────
# 12V input: Fuse + P-MOS reverse protection + TVS
f1 = Part("Device", "Fuse", value="5A", footprint="Fuse:Fuse_BL5AG")
q1 = Part("Transistor_FET", "AO4407A", value="AO4407A")  # P-MOS
r1 = Part("Device", "R", value="10k")
r2 = Part("Device", "R", value="100k")
d1 = Part("Device", "D_TVS", value="SMBJ15A")
d2 = Part("Device", "D_Zener", value="1N4744A")

# Connections (simplified - see DESIGN.md §2.1)
# 12V_IN -> F1 -> Q1 source, Q1 drain -> 12V_BUS
# Q1 gate <- R1(10k to GND), R2(100k to 12V_IN)
# D1 across 12V_BUS to GND, D2 gate-source protection

# ── DC-DC Buck 12V → 5V ───────────────────────────────────────────────
u1 = Part("Regulator_Linear", "MP1584", value="MP1584EN")
l1 = Part("Device", "L", value="47uH")
c1 = Part("Device", "C", value="10uF")
c2 = Part("Device", "CP", value="220uF")
c3 = Part("Device", "C", value="22uF")
c4 = Part("Device", "CP", value="220uF")
r3 = Part("Device", "R", value="68k")
r4 = Part("Device", "R", value="13k")
c5 = Part("Device", "C", value="100nF")

# ── LDO 5V → 3.3V ─────────────────────────────────────────────────────
u2 = Part("Regulator_Linear", "AMS1117-3.3", value="AMS1117-3.3")
c6 = Part("Device", "C", value="10uF")
c7 = Part("Device", "C", value="10uF")
d3 = Part("Device", "LED", value="Green")
r5 = Part("Device", "R", value="1k")

# ── ESP32 DevKitC Carrier ─────────────────────────────────────────────
# 2x19 pin female headers (DevKitC plugs in here)
j_dev1 = Part("Connector_Generic", "Conn_01x19", value="DevKitC_Left")
j_dev2 = Part("Connector_Generic", "Conn_01x19", value="DevKitC_Right")

# DevKitC pin mapping (1-indexed in SKiDL):
# J_DEV1: 1=3V3, 2=GND, 5=GPIO4(1-Wire), 6=GPIO16(RX2), 7=GPIO17(TX2),
#         8=GPIO5(MOS1), 9=GPIO18(MOS3), 10=GPIO19(MOS4), 11=GPIO21(SDA),
#         14=GPIO22(SCL), 15=GPIO23(WS2812), 16=GPIO13(DIN1), 18=VIN(5V)
# J_DEV2: 5=GPIO14(MOS2), 6=GPIO27(PUMP_STOP), 7=GPIO26(SV2), 8=GPIO25(SV1),
#         10=GPIO32(DIN6), 11=GPIO35(DIN3), 12=GPIO34(DIN2), 13=GPIO39(DIN5),
#         14=GPIO36(DIN4)

# I²C bus nets
sda = Net("SDA")
scl = Net("SCL")

# ── I²C Pull-ups ──────────────────────────────────────────────────────
r6 = Part("Device", "R", value="4.7k")   # SDA pullup
r7 = Part("Device", "R", value="4.7k")   # SCL pullup
r6[1] & v33; r6[2] & sda
r7[1] & v33; r7[2] & scl

# ── 1-Wire ────────────────────────────────────────────────────────────
one_wire = Net("1WIRE_DATA")
r8 = Part("Device", "R", value="4.7k")
r8[1] & v33; r8[2] & one_wire

# ── Digital Input Conditioning (6 channels) ───────────────────────────
# Each: 10k pullup + 1k series + 100nF filter + BAT54S clamp
din_nets = [Net(f"DIN{i+1}") for i in range(6)]
din_gpios = [13, 32, 34, 35, 36, 39]  # GPIO numbers

for i in range(6):
    r_pull = Part("Device", "R", value="10k", dest=TEMPLATE)
    r_ser = Part("Device", "R", value="1k", dest=TEMPLATE)
    c_filt = Part("Device", "C", value="100nF", dest=TEMPLATE)
    d_clamp = Part("Device", "D_Schottky", value="BAT54S", dest=TEMPLATE)

    # Pullup to 3.3V
    r_pull[1] & v33
    r_pull[2] & din_nets[i]
    # RC filter
    c_filt[1] & din_nets[i]
    c_filt[2] & gnd
    # Series resistor to GPIO
    r_ser[1] & din_nets[i]

# ── Level Shifters (2x BSS138 for pulse inputs CH2/CH3) ──────────────
for i in range(2):
    q_lvl = Part("Transistor_FET", "BSS138", value="BSS138")
    r_5v = Part("Device", "R", value="10k")
    r_33v = Part("Device", "R", value="10k")
    # BSS138: Gate→3.3V, Source→3.3V side (GPIO), Drain→5V side (sensor)
    # See DESIGN.md §6.2 for detailed connection

# ── MOSFET Outputs (4x IRLZ44N low-side) ──────────────────────────────
for i in range(4):
    q_mos = Part("Transistor_FET", "IRLZ44N", value="IRLZ44N")
    d_fly = Part("Device", "D", value="1N5819")
    r_gate = Part("Device", "R", value="100R")
    r_pd = Part("Device", "R", value="10k")
    d_mos = Part("Device", "LED", value="Red")
    r_mosled = Part("Device", "R", value="1k")
    # MOSFET: Gate←R_gate←GPIO, Gate←R_pd→GND, Drain→Load-, Source→GND
    # Flyback diode across load terminals
    # See DESIGN.md §7

# ── Servo Headers (2x) ────────────────────────────────────────────────
for i in range(2):
    j_sv = Part("Connector_Generic", "Conn_01x03", value=f"SV{i+1}")
    r_sv = Part("Device", "R", value="1k")
    # Pin 1=5V, Pin 2=GND, Pin 3=PWM

# ── WS2812 (via BSS138 level shifter) ─────────────────────────────────
q_ws = Part("Transistor_FET", "BSS138", value="BSS138")
r_ws1 = Part("Device", "R", value="100R")
r_ws2 = Part("Device", "R", value="4.7k")

# ── PZEM UART (2x BSS138 level shifters) ──────────────────────────────
for label in ["TX", "RX"]:
    q_uart = Part("Transistor_FET", "BSS138", value="BSS138")
    r_33 = Part("Device", "R", value="10k")
    r_5 = Part("Device", "R", value="10k")

# ── INA226 (12V bus monitoring) ───────────────────────────────────────
u_ina = Part("Sensor_Voltage", "INA226", value="INA226")
r_shunt = Part("Device", "R_Shunt", value="0.01R")
c_ina = Part("Device", "C", value="100nF")
# INA226: V+→12V_BUS, V-→12V_LOAD, SDA→I²C, SCL→I²C, A0/A1→GND

# ── ADS1115 (Analog sensor ADC) ───────────────────────────────────────
u_ads = Part("Analog_ADC", "ADS1115", value="ADS1115")
c_ads = Part("Device", "C", value="100nF")
# ADS1115: A0←pH, A1←TDS, A2←Turbidity, ADDR→GND

# ── MCP23017 (I²C I/O expander) ───────────────────────────────────────
u_mcp = Part("Driver_IO_expander", "MCP23017", value="MCP23017")
c_mcp = Part("Device", "C", value="100nF")
# GPA0-GPA2: probe power CH1-3, A0/A1/A2→GND (addr 0x20)

# ── Probe Power Switches (3x SI2302) ──────────────────────────────────
for i in range(3):
    q_probe = Part("Transistor_FET", "SI2302", value="SI2302")
    r_pd = Part("Device", "R", value="10k")
    # Gate←MCP23017 GPA{i}, Drain→V_PROBE, Source→GND

# ── Pump Control (PUMP_STOP, opto-isolated) ───────────────────────────
u_opto = Part("Isolator", "PC817", value="PC817")
r_led = Part("Device", "R", value="330R")
r_pull = Part("Device", "R", value="10k")
# GPIO27 → R_led(330) → PC817 LED+ → LED- → GND
# Output: isolated, NO/NC jumper, default NO

# ── High Water Float Safety (independent of MCU) ──────────────────────
u_opto2 = Part("Isolator", "PC817", value="PC817")
r_hw = Part("Device", "R", value="1k")
# 12V → R_hw(1k) → PC817 LED+ → LED- → float NC → GND
# NC contacts in relay coil / opto input (low voltage, NOT 220V)

# ── BME280 (onboard, optional) ────────────────────────────────────────
u_bme = Part("Sensor", "BME280", value="BME280")
c_bme = Part("Device", "C", value="100nF")

# ── Connectors ────────────────────────────────────────────────────────
j_12v = Part("Connector_Generic", "Conn_01x02", value="12V_IN")
j_i2c = Part("Connector_Generic", "Conn_01x04", value="I2C_BUS")
j_1w = Part("Connector_Generic", "Conn_01x03", value="1WIRE")
j_pump = Part("Connector_Generic", "Conn_01x03", value="PUMP_CTRL")
j_hw = Part("Connector_Generic", "Conn_01x02", value="HIGH_WATER")

# 6x digital input terminals
j_din = [Part("Connector_Generic", "Conn_01x02", value=f"DIN{i+1}") for i in range(6)]
# 4x MOSFET output terminals
j_mos = [Part("Connector_Generic", "Conn_01x02", value=f"MOS{i+1}") for i in range(4)]
# 4x PZEM header
j_pzem = Part("Connector_Generic", "Conn_01x04", value="PZEM_UART")
# 1x WS2812 header
j_ws = Part("Connector_Generic", "Conn_01x03", value="WS2812")
# 6x probe power header
j_prb = Part("Connector_Generic", "Conn_01x06", value="PROBE_PWR")

# ── Generate Netlist ──────────────────────────────────────────────────
output_file = os.path.join(os.path.dirname(__file__), "..", "export", "node-baseboard.net")
os.makedirs(os.path.dirname(output_file), exist_ok=True)

generate_netlist(output_file)
print(f"Netlist generated: {output_file}")
print(f"Total parts: {len(default_circuit.parts)}")
print(f"Total nets: {len(default_circuit.nets)}")
