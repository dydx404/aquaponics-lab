# hardware · 电子

接线图、引脚分配、原理图、电源分配。

## 内容（规划）

- `node-tank01-wiring.*` — 首个节点接线图（DS18B20 / INA219 / 浮球）。
- `power-bus.*` — 12V DC 母线、降压、保险、太阳能接入。
- `pinout-*.md` — 各节点 ESP32 引脚分配表（与 `firmware/esphome/*.yaml` 顶部注释一致）。

## 约定

- 优先低压 12V DC；市电（220V）必须漏电保护 + 滴水弯。
- 入水接头用航空插头（GX12/16）防水可插拔。
- 原理图源文件（KiCad 等）放此处，导出 PDF/PNG 放同目录。

TODO：MVP-4 补 node-tank01 接线图。
