# 交接 · node-baseboard PCB —— WorkBuddy 设计 / Claude Code 审核

> 2026-08-08 分工更新:PCB **设计交给 WorkBuddy**,**审核归 Claude Code**。
> 物理 bring-up(焊接/上电/冒烟)= 广州(用户)或福州(EEE 同学),二选一。

## 先读(全是已定的决定,别重造轮子)

- **任务书 + 边界**:本目录 [README.md](README.md) 第 2/3 节(硬约束 + MoSCoW 规格)
- **接口契约** ⭐:[docs/handbook/13-interfaces.md](../../../docs/handbook/13-interfaces.md)(你的边界)
- **引脚基准**:[docs/handbook/21-appendix-pinouts.md](../../../docs/handbook/21-appendix-pinouts.md)(21.1 已是经典 ESP32 引脚)
- **关键 ADR**:[0004](../../../docs/decisions/0004-power-domains.md) 供电分域 · [0007](../../../docs/decisions/0007-sensor-rail-and-level-translation.md) 传感轨+电平转换 · [0008](../../../docs/decisions/0008-node-io-provisioning.md) 节点 I/O · [0009](../../../docs/decisions/0009-pump-metering-and-control.md) 泵计量与控制 · **[0011](../../../docs/decisions/0011-standard-node-board-selection.md) 开发板 = 经典 ESP32-WROOM-32 DevKitC(38 脚)**

## 板子(ADR-0011 已定)

标准节点板 = **载板**:插一块经典 **ESP32-WROOM-32 DevKitC(38 脚)**。射频在模块内 → **载板不碰 RF,2 层板足够**,自动布线可用。

## 工具

用你能驱动的:**嘉立创EDA专业版 + EasyEDA Copilot(MCP)** 最顺(元件走 LCSC 库=封装现成、一键 JLC 打样);没有就 KiCad 出稿再导入 JLC。**交付物比工具重要。**

## 交付物(便于审核)

1. 原理图 PDF(分区清晰、可读)
2. EDA 工程源文件 / 网表(进 git)
3. BOM(CSV,**带 LCSC 型号**)
4. 引脚映射表:板上每个接口 ↔ ESP32 GPIO ↔ 契约
5. **自检表**:对照下面「审核门禁」逐条打勾
6. (打样前)Gerber + 3D 预览截图 + DRC 报告

## 审核门禁(Claude Code 会逐条查 —— 这也是你的自检表)

### 安全(任一不过 = 否决)
- [ ] 12V 输入:保险 + 防反接(P-MOS 或肖特基)+ TVS
- [ ] 每路感性负载 MOSFET 必带 **续流二极管** + 栅极下拉
- [ ] 泵控制:**光耦隔离 + 高有效**,网络名 `PUMP_STOP`;**禁止低有效**(上电浮空→误吸合);NO/NC 跳线,**交付默认 = NO(泵默认关)**([ADR-0009](../../../docs/decisions/0009-pump-metering-and-control.md) R-1)
- [ ] 主泵 **220V 不上板**,板上只出隔离控制信号([ADR-0004](../../../docs/decisions/0004-power-domains.md))
- [ ] 高水位浮球串 **继电器线圈/光耦输入(低压)**,**严禁串 220V**([ADR-0009](../../../docs/decisions/0009-pump-metering-and-control.md) R-2)

### 契约 / 功能
- [ ] 引脚符合附录 21.1(I²C=GPIO21/22、1-Wire=GPIO4、低水位浮球=GPIO13)
- [ ] I²C 带上拉、仅盒内;模拟量一律经 **ADS1115**([ADR-0006](../../../docs/decisions/0006-i2c-cable-limits.md)/[0007](../../../docs/decisions/0007-sensor-rail-and-level-translation.md))
- [ ] 传感轨 3.3V;**5V 器件过电平转换**(YF-S201 流量、超声 Echo、PZEM UART)([ADR-0007](../../../docs/decisions/0007-sensor-rail-and-level-translation.md)/[0008](../../../docs/decisions/0008-node-io-provisioning.md))
- [ ] ≥6 路调理数字输入(GPIO34–39 外部上拉 + RC + 限流 + 钳位);≥2 路 5V 脉冲输入([ADR-0008](../../../docs/decisions/0008-node-io-provisioning.md))
- [ ] ≥2 路(预留 ~4)低边 MOSFET 12V 轻载;2 舵机头;WS2812;PZEM **UART header**;**INA226 测 12V 母线**;3 路开关式探头供电([ADR-0009](../../../docs/decisions/0009-pump-metering-and-control.md) R-6 时序在固件)
- [ ] 连接器无关:v0.1 用端子排/排针,**不焊死 GX**

### 可制造
- [ ] 元件尽量用 **LCSC 库件**(封装已验证);自建封装需显式标注核对
- [ ] DRC 无致命错误;2 层;丝印标全接口/极性/**失电默认态**
- [ ] **打样前**:3D 预览 + DRC 报告先给 Claude Code 过一遍 **再下单**

## 心态

第一版是**学习板**,预算里留一次改版(v2),先打 5 片最便宜档。审核只卡**安全 + 契约**,板内设计你自由发挥。
