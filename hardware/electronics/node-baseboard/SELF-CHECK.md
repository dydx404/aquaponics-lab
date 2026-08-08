# node-baseboard v0.1 — 自检表

> 对照 [handoff-workbuddy.md](handoff-workbuddy.md) 审核门禁, 逐条打勾。
> Claude Code 审核时会逐条查 — 这也是你的自检表。

## 审核修正 (Claude Code review v2)

| # | 审核意见 | 状态 | 修正内容 |
|---|----------|------|----------|
| R-1 | 3.3V 轨双源冲突 | ✅ | DevKitC 3V3 pin 标 NC, 板上 3.3V 传感轨独立 (DESIGN.md §2.3) |
| R-2 | GPIO5 strapping 脚不可接 MOSFET 下拉 | ✅ | MOSFET CH1 移到 GPIO33; GPIO5 改为超声 Trig (无下拉) |
| R-3 | P-MOS 防反接方向写反 | ✅ | Drain=输入+, Source=负载侧 (体二极管反接时反偏截止) |
| R-4 | INA226 LCSC 编号截断 | ✅ | C8Z → C49851 (INA226AIDGSR); 分流满量程 ±81.92mV |
| R-5 | 超声波缺 Trig | ✅ | GPIO5 作为 Trig 输出 (strapping, 无下拉, boot=HIGH) |
| R-6 | GPIO27 加下拉 | ✅ | R_pd_pump 10kΩ 到 GND, boot 时光耦 LED 确保关 |
| R-7 | 5V 预算 | ✅ | 丝印标注 "大舵机建议外接 5V"; 可割线+跳线隔离 |
| R-8 | LCSC 全表核对 | ⏳ | 导入 EDA 时逐个确认有货+有封装 |

## 安全门禁 (任一不过 = 否决)

| # | 检查项 | 状态 | 实现位置 | 备注 |
|---|--------|------|----------|------|
| S1 | 12V 输入: 保险 + 防反接(P-MOS) + TVS | ✅ | DESIGN.md §2.1 | F1(5A) + Q1(AO4407A) + D1(SMBJ15A) |
| S2 | 每路感性负载 MOSFET 带续流二极管 | ✅ | DESIGN.md §7 | D_fly(1N5819) × 4 |
| S3 | 每路 MOSFET 栅极下拉 | ✅ | DESIGN.md §7 | R_pd(10kΩ) × 4, 确保 GPIO 浮空时截止 |
| S4 | 泵控制: 光耦隔离 + 高有效 | ✅ | DESIGN.md §14 | U_OPTO(PC817), GPIO27 HIGH = 停泵 |
| S5 | 泵控制: 网络名 = PUMP_STOP | ✅ | DESIGN.md §14 | 网络名/丝印/契约均用 PUMP_STOP |
| S6 | 泵控制: 禁止低有效 | ✅ | DESIGN.md §14 | 高有效: GPIO HIGH → 光耦导通 → 停泵 |
| S7 | 泵控制: NO/NC 跳线, 交付默认 = NO (泵关) | ✅ | DESIGN.md §14 | JP_NCNO 默认 NO, 丝印 "NC 需前提①②③" |
| S8 | 主泵 220V 不上板 | ✅ | DESIGN.md §14 | 只出隔离控制信号到端子 |
| S9 | 高水位浮球串低压回路, 不串 220V | ✅ | DESIGN.md §15 | U_OPTO2(PC817) 串光耦输入, 12V 侧 |

## 契约 / 功能门禁

| # | 检查项 | 状态 | 实现位置 | 备注 |
|---|--------|------|----------|------|
| C1 | 引脚符合附录 21.1: I²C=GPIO21/22 | ✅ | PIN-MAPPING.md §1 | SDA=21, SCL=22 |
| C2 | 引脚符合附录 21.1: 1-Wire=GPIO4 | ✅ | PIN-MAPPING.md §1 | DS18B20 |
| C3 | 引脚符合附录 21.1: 浮球=GPIO13 | ✅ | PIN-MAPPING.md §1 | 低水位浮球 CH1 |
| C4 | I²C 带上拉 | ✅ | DESIGN.md §4 | R6/R7 = 4.7kΩ to 3.3V |
| C5 | I²C 仅盒内 (≲30cm) | ✅ | DESIGN.md §4 | 板内布线, 对外走 J_I2C 短线 |
| C6 | 模拟量一律经 ADS1115 | ✅ | DESIGN.md §12 | pH/TDS/浊度 → ADS1115 A0/A1/A2 |
| C7 | 传感轨 3.3V | ✅ | DESIGN.md §2.3 | AMS1117-3.3 → 3.3V 传感轨 |
| C8 | 5V 器件过电平转换 | ✅ | DESIGN.md §6.2/§9/§10 | BSS138 × 5 (2 脉冲 + WS2812 + 2 UART) |
| C9 | ≥6 路调理数字输入 | ✅ | DESIGN.md §6 | 6 路 (GPIO13/32/34/35/36/39) |
| C10 | GPIO34-39 外部上拉 + RC + 限流 + 钳位 | ✅ | DESIGN.md §6.1 | 10kΩ + 1kΩ + 100nF + BAT54S |
| C11 | ≥2 路 5V 容忍脉冲输入 | ✅ | DESIGN.md §6.2 | CH2(GPIO34) + CH3(GPIO35), 经 BSS138 |
| C12 | ≥2 路(预留4)低边 MOSFET 12V 轻载 | ✅ | DESIGN.md §7 | 4 路 IRLZ44N + 续流 + 下拉 |
| C13 | 2 舵机头 | ✅ | DESIGN.md §8 | J_SV1(GPIO25) + J_SV2(GPIO26) |
| C14 | WS2812 口 | ✅ | DESIGN.md §9 | GPIO23 经 BSS138 电平转换 |
| C15 | PZEM UART header | ✅ | DESIGN.md §10 | GPIO16/17 UART2, 经 BSS138 |
| C16 | INA226 测 12V 母线 | ✅ | DESIGN.md §11 | I²C 0x40, R_shunt=0.01Ω |
| C17 | 3 路开关式探头供电 | ✅ | DESIGN.md §12.1 | MCP23017 GPA0/1/2 → SI2302 × 3 |
| C18 | 连接器: v0.1 用端子排/排针 | ✅ | DESIGN.md §17 | KF128 端子 + 排针, 不焊死 GX |

## 可制造门禁

| # | 检查项 | 状态 | 实现位置 | 备注 |
|---|--------|------|----------|------|
| M1 | 元件尽量用 LCSC 库件 | ✅ | bom.csv | 全部 LCSC 型号 |
| M2 | DRC 无致命错误 | ⏳ | 待 PCB 布板后验证 | 设计文档已标注约束 |
| M3 | 2 层板 | ✅ | DESIGN.md §18 | Top 信号+元件, Bottom GND+信号 |
| M4 | 丝印标全接口/极性/引脚号 | ✅ | DESIGN.md §18 | 含失电默认态标注 |
| M5 | 丝印标注 PUMP_STOP 失电默认态 | ✅ | DESIGN.md §14 | "高=停泵, 默认NO=关" |
| M6 | 打样前: 3D 预览 + DRC 报告给 Claude Code | ⏳ | 待 PCB 布板后 | 先过审再下单 |

## 附加 (Should 项)

| # | 检查项 | 状态 | 实现位置 | 备注 |
|---|--------|------|----------|------|
| A1 | MCP23017 I²C 扩展 | ✅ | DESIGN.md §13 | 0x20, 探头供电 + 备用 |
| A2 | 高水位浮球独立断泵 (不经 MCU) | ✅ | DESIGN.md §15 | U_OPTO2 串联在控制回路 |
| A3 | 电源指示灯 | ✅ | DESIGN.md §2.3 | D3 绿色 LED |
| A4 | MOSFET 状态指示灯 | ✅ | DESIGN.md §7 | D_mos 红色 LED × 4 |
| A5 | 安装孔 | ✅ | DESIGN.md §18 | 4× M3 (φ3.2mm) |

## 状态图例

- ✅ 已完成 (设计层)
- ⏳ 待 PCB 布板后验证
- ❌ 未完成 (需补充)
