# 第 21 章 · 附录：引脚 / 接线 / 地址表

> 演进中。**这是硬件与固件的对表基准**，改动即接口变更（[第 13 章](13-interfaces.md)），需 ADR + 双方确认。

## 21.1 node-tank01 引脚分配（示例）

| GPIO | 功能 | 器件 |
|---|---|---|
| GPIO4 | 1-Wire | DS18B20 水温 |
| GPIO21 | I²C SDA | INA226（12V 母线/电池电流） |
| GPIO22 | I²C SCL | INA226 |
| GPIO13 | 数字输入(上拉) | 浮球开关（低水位） |

> ESP32 strapping/受限脚（GPIO0/2/12/15 等）避免用作关键输入输出；具体见 ESP32 数据手册。

## 21.2 I²C 地址分配表

| 器件 | 默认地址 | 可选 | 备注 |
|---|---|---|---|
| ADS1115 | 0x48 | 0x49/4A/4B | ADDR 脚选址 |
| INA226 | 0x40 | 0x41–0x4F | A0/A1 选址（泵功率走 PZEM/UART，不在 I²C） |
| BME280 | 0x76 | 0x77 | |
| BH1750 | 0x23 | 0x5C | |
| DS3231 | 0x68 | — | |
| TCA9548A(复用) | 0x70 | 0x71–0x77 | 地址冲突时用 |

## 21.3 航空插头针脚（契约草案）

| 插头 | 针 | 信号 |
|---|---|---|
| GX16-4（传感） | 1 / 2 / 3 / 4 | +5V / GND / SDA或信号 / SCL或信号 |
| GX12-2（12V 负载） | 1 / 2 | +12V / GND |

## 21.4 开孔尺寸（塑料桶）

| 管径 | Uniseal 开孔 | 水箱接头开孔 |
|---|---|---|
| 20mm(4分) | ~32mm | 4分 → ~22mm |
| 25mm(6分) | ~40–43mm | 6分 → ~28mm |
| 32mm(1寸) | ~50mm | 1寸 → ~34mm |
| 50mm | ~68–73mm | — |

> 以接头卖家标注为准，各家差 1–2mm。

## 21.5 MQTT 主题总表（随节点上线补全）

| 主题 | 类型 | 单位 | 来源 |
|---|---|---|---|
| `aqua/tank01/water_temp` | 遥测 | °C | DS18B20 |
| `aqua/tank01/low_water` | 布尔 | ON/OFF | 浮球开关(低水位) |
| `aqua/tank01/pump_power` | 遥测 | W | PZEM-004T(220V AC 泵) |
| `aqua/tank01/pump_energy` | 遥测 | kWh | PZEM-004T |
| `aqua/tank01/bus_12v_i` | 遥测 | A | INA226(12V 母线/电池) |
| `aqua/power/battery_v` | 遥测 | V | INA226 |
| `aqua/<node>/<actuator>/state` | 状态回读 | ON/OFF | 执行器 |
| `aqua/<node>/status` | LWT | online/offline | ESPHome |
| `aqua/<node>/<actuator>/set` | 命令 | — | HA |
