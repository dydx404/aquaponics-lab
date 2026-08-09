# WorkBuddy node-baseboard 自动化产物（WIP / 半成品）

> 本目录存放 WorkBuddy 用 **EasyEDA Pro WebSocket Bridge** 自动生成 node-baseboard
> 原理图时产出的脚本与中间数据。**尚未完成连线与出图**，先提交保存进度。

## 背景

- 目标：在 `aqualab.eprj2` 的 node-baseboard 原理图页里，按 PR #5 的
  `DESIGN.md` / `PIN-MAPPING.md` 完成 133 个元件的放置、连线、导出。
- 元件已通过 Bridge 在 EasyEDA Pro 内放置（designator 已自动标注，LCSC 料号保留，
  满足制造合规 R-8），但**布局被撒在一个 ~34000×8400 单位的超大画布上，远超出
  A4 页面**，且连线尚未执行。

## 本目录文件

| 文件 | 作用 |
|------|------|
| `eda_bridge.py` | Bridge 调用封装：向 EasyEDA Pro（localhost:49620）POST `/execute`，执行 `async function(eda){...}` 代码。 |
| `build_manifest.py` | 由 PR #5 元件清单生成 133 实例 `manifest.json`（id→type→lib UUID 映射）。 |
| `run_place.py` | 调 Bridge 按 `manifest.json` 批量放置元件。 |
| `run_extract.py` | 分块（每批 15）调 `sch_PrimitiveComponent.getAllPinsByPrimitiveId` 提取 133 元件全部引脚页面坐标 → `pins_raw.json`。 |
| `build_pins.py` | 合并 manifest/placement/pins_raw → `pins.json`（含每个引脚的 `lx/ly` 页面坐标）。 |
| `build_nets2.py` | **权威网表生成器**：直接从 PR #5 的 `DESIGN.md`/`PIN-MAPPING.md` 映射到真实引脚名，输出 `nets2.json`（54 网 / 361 端点，0 悬空，已通过 12V/5V 隔离检查）。 |
| `manifest.json` | 133 个实例（id / type / lib UUID）。 |
| `placement.json` | 放置后的坐标（散落布局）。 |
| `pins.json` | 133 元件全部引脚的真实页面坐标（连线依据）。 |
| `pins_raw.json` | 提取原始数据。 |
| `nets2.json` | **权威网表**，连线阶段应以此为准。 |
| `type_uuids.json` | 元件类型 → 嘉立创基础库 UUID 映射。 |
| `id2desig.json` | 实例 id → designator 映射。 |

## 已发现并修复的关键坑（供后续接续）

1. **引脚坐标可达**：`sch_PrimitiveComponent.getAllPinsByPrimitiveId(pid)` 返回每脚
   `x/y`（页面坐标）、`pinNumber`、`pinName`、`rotation`、`pinLength`。这是打通连线的前提。
2. **Bridge 调用不稳定**：`--file` 传 .js 大循环常 500，改用 `inline --code "$(cat x.js)"`
   并分块（每批 ≤15）可靠。
3. **不要的 namespaces**：`sch_PrimitivePin` 是空对象；`sch_PrimitiveNetLabel`/
   `NetPort`/`Junction` 不存在；`sch_Netlist` 的 `getNetlist` 会 500；
   `createNetFlag` 参数过于挑剔无法简易使用。因此连通性只能靠导线实际接触。
4. **旧 `nets.json`（首次尝试）系统性错误**：地址脚悬空、12V_BUS 被 5V/3.3V 元件
   污染（12V-5V 短路风险）、BSS138 电平转换被短接、DevKitC 3V3 未按 R-1 设 NC。
   → 已弃用，改用 `nets2.json`。
5. **元件实际引脚名与你文档不符的点**：
   - MCP23017 实际是 `SCK`（非 `SCL`）；INA226/ADS1115 仍是 `SCL`/`SDA`。
   - BME280 实际放的是 **SPI 版符号**（无 SDA/SCL，只有 SDO/SDI/SCK/CSB）。
   - R_shunt 是开尔文 4 端电阻（`I1/I2` 电流端，`E1/E2` 取样端）。
   - J_PZEM/J_I2C 实际 6 脚、J_1W 实际 5 脚（文档写少）。

## 阻塞 / 下一步（未完成）

- ❌ **布局重排**：当前元件散落在 A4 页面之外，连线前需按功能分区做紧凑重布局
  （约 134 元件，x 步进 560 但含 4200+ 大跳变）。
- ❌ **连线**：以 `nets2.json` 为权威，用 `sch_PrimitiveWire.create({x1,y1,x2,y2})`
  按网连线（comb 方案：每网一根水平干线 + 各引脚垂下；干线 Y 互不重合以避免误连）。
- ❌ **ERC / 导出 / 提交 PR #5 供 Claude Code 审核**。
- EasyEDA Pro 工程（`aqualab.eprj2`）本身在 EasyEDA 应用内，不属于本 git 仓库；
  本目录只保存工具链与提取数据。

## 复现

```bash
# 需 EasyEDA Pro 打开 aqualab 工程且 Bridge 监听 localhost:49620
python build_manifest.py     # -> manifest.json
python run_place.py          # 放置（已在 EasyEDA 内执行过）
python run_extract.py        # -> pins_raw.json
python build_pins.py         # -> pins.json
python build_nets2.py        # -> nets2.json（校验 0 错误）
```
