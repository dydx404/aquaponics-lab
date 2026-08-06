# ADR-0008 · 节点 I/O 供给：数字输入 / 脉冲 / 专用 header + GPIO 预算

- 状态：已采纳
- 日期：2026-08-06
- 来源：硬件设计评审（EE）P0-4 / §2.4

## 背景

评审指出：`node-baseboard` 的 Must 清单**零个数字输入通道**，但

- [`node-tank01.yaml`](../../firmware/esphome/node-tank01.yaml) 已经在用 GPIO13 浮球开关；
- [第 16 章](../handbook/16-testing.md) MVP-4 验收要"水温/**水位**/泵流上 HA、拔泵手机响"；
- [第 7 章](../handbook/07-sensors.md) §7.5.1 把"浮球缺水兜底"列为失效安全（呼应铁律一）。

**照现规格打的板，MVP-4 验收过不了。** 这是需求遗漏，不是理解偏差。

## 决定

- **Must 加 ≥6 路调理数字输入**（浮球/漏水等干接点）：外部上拉（GPIO34–39 只输入且**无内部上拉**，板上必须给）+ RC 滤波 + 串联限流 + 钳位二极管；湿区干接点防浪涌。
- 其中 **≥2 路 5V 容忍脉冲输入**（YF-S201 流量、超声波 Echo，经电平转换）。
- **预留专用 header**：HX711（DT/SCK）、舵机 PWM（独立供电）、步进（STEP/DIR/EN）、WS2812（+ 电平转换）。
- **GPIO 预算 + ESP32 陷阱登记到 [第 21 章附录](../handbook/21-appendix-pinouts.md)**：GPIO6–11 接 Flash 不可用；GPIO34–39 只输入、无内部上拉；ADC2（含 GPIO0/2/4/12–15/25–27）WiFi 开启时不可用 → 模拟量必须走 ADS1115。

## 理由

补齐 functional-spec 已列、`node-tank01` 已用的功能；数字输入是 MVP-4 的前提；每路约 ¥1 + 被动件，6 路 ≈ ¥6 换回 4 项功能可达。

## 后果

- node-baseboard Must 扩充（数字输入 + 脉冲 + 专用 header）。
- GPIO 够用但无余量 → 支持"尽量用 I²C 器件 / 板上留 I²C 扩展"。
