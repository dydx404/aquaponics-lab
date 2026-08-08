# ADR-0011 · 标准节点板选型 = 经典 ESP32-WROOM-32 DevKitC

- 状态：已采纳
- 日期：2026-08-08
- 来源：用户实物盘点 + 委托软件/集成方拍板（替代任务书「开发板选型你定」的长期悬置）

## 背景

任务书（[node-baseboard](../../hardware/electronics/node-baseboard/README.md)）与 [functional-spec](../functional-spec.md) 一直把**开发板选型**留给硬件方，唯一约束是"ESPHome 兼容的 ESP32 家族"。这让**载板（node-baseboard）的开发板座 footprint 目标板一直悬空**——而载板的排针 footprint + 引脚映射必须绑定到某一块具体的开发板。

与此同时，固件 `firmware/esphome/node-tank01.yaml`（`board: esp32dev`）与[附录 21.1](../handbook/21-appendix-pinouts.md) 其实**早已隐含按经典 ESP32 引脚写**（GPIO21/22 做 I²C、GPIO4 1-Wire、GPIO13 浮球）。

曾一度倾向 ESP32-C3。但用户实物盘点：手上有 **2× 经典 ESP32-WROOM-32 DevKitC（AZ-Delivery）+ 1× ESP32-S3-N16R8（16MB Flash/8MB PSRAM）**，**没有 C3**。用户委托软件/集成方按实物拍板。

## 决定

1. **标准节点板 = 经典 ESP32-WROOM-32 DevKitC（38 脚）。** 具体买哪家、哪块便宜的 WROOM-32 DevKitC 由硬件方按货源定（同为 WROOM-32 DevKitC 即可，footprint 一致）。
2. **ESP32-S3-N16R8 保留给以后的视觉/CV/墨水屏终端节点**（8MB PSRAM + 原生 USB 正对口），不做标准传感节点。
3. **不采用 ESP32-C3**（手上没有；且见下方理由）。

## 理由

- **零采购、立刻能起真节点**：直接用手上 2 块，首个 `node-tank01` 面包板节点可马上替换模拟器。
- **零固件/文档改动**：固件与附录本来就是经典 ESP32 引脚，GPIO21/22（I²C）、GPIO4（1-Wire）、GPIO13（浮球）在 WROOM-32 全部有效。反观 C3：**没有 GPIO13**（C3 只有 GPIO0–10、18–21）、I²C 默认脚不同，选它反而要把附录 + 固件全部重映射。
- **载板最省事**：38 脚 DevKitC 是 KiCad 标准封装；GPIO 数量足以覆盖 [ADR-0008](0008-node-io-provisioning.md) 的 ≥6 路数字输入 + 预留执行器。对初学做第一块载板的硬件方最友好。
- **不浪费 S3**：S3 的 PSRAM/原生 USB 用在纯传感节点是浪费，留给真正需要它的视觉节点。

## 后果

- **载板（node-baseboard）**：开发板座按 **WROOM-32 DevKitC 38 脚** footprint 设计。⚠️ 注意宽体变种（~25.4mm 宽）会占满标准面包板中沟——做载板/面包板自测时用两块面包板拼接、或选窄体变种；硬件方自行确认所购变种尺寸。
- **附录 21.1**：**已符合（经典 ESP32 引脚），无需改动**；仅建议补一句"目标板 = WROOM-32 DevKitC"注脚——归**硬件方在其 PR 里补**（附录是硬件对表基准，避免并行代改，见 [§13.6](../handbook/13-interfaces.md)）。
- **任务书** node-baseboard「开发板座（开发板选型你定）」一行 → 由**硬件方 PR 更新**为本 ADR 决定。
- **固件** `node-tank01.yaml` / `common/base.yaml`：`board: esp32dev` 不变，无需改；先前给出的面包板接线（21/22/4/13）仍然正确。
- S3 视觉节点的引脚分配将来在附录另开一节（21.x）。
