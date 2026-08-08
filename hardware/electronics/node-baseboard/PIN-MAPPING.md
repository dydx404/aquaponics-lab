# node-baseboard v0.1 — 引脚映射表

> 对照 [接口契约 §13](../../../docs/handbook/13-interfaces.md) 和 [附录 21.1](../../../docs/handbook/21-appendix-pinouts.md)
> 开发板: ESP32-WROOM-32 DevKitC 38 脚 (ADR-0011)

## 1. ESP32 GPIO ↔ 板上功能 ↔ 契约

| GPIO | 方向 | 板上功能 | 外部器件/连接器 | 契约引用 | 电平 | 备注 |
|------|------|----------|----------------|----------|------|------|
| GPIO4 | OUT | 1-Wire | J_1W → DS18B20 | 附录 21.1 | 3.3V | 4.7kΩ 上拉 |
| GPIO5 | OUT | MOSFET CH1 | J_MOS1 → 12V 风扇 | functional-spec B | 3.3V | IRLZ44N 低边 |
| GPIO13 | IN | 数字输入 CH1 | J_DIN1 → 低水位浮球 | 附录 21.1 ⭐ | 3.3V | 上拉+RC+钳位 |
| GPIO14 | OUT | MOSFET CH2 | J_MOS2 → 12V 阀/打氧 | functional-spec B | 3.3V | IRLZ44N 低边 |
| GPIO16 | IN | UART2 RX | J_PZEM ← PZEM TX | ADR-0009 R-5 | 3.3V | 经 BSS138 转换 |
| GPIO17 | OUT | UART2 TX | J_PZEM → PZEM RX | ADR-0009 R-5 | 3.3V | 经 BSS138 转换 |
| GPIO18 | OUT | MOSFET CH3 | J_MOS3 → 12V 灯 | functional-spec B | 3.3V | IRLZ44N 低边 |
| GPIO19 | OUT | MOSFET CH4 | J_MOS4 → 12V 备用 | functional-spec B | 3.3V | IRLZ44N 低边 |
| GPIO21 | I/O | I²C SDA | INA226/ADS1115/MCP23017/BME280 | 附录 21.1 ⭐ | 3.3V | 4.7kΩ 上拉 |
| GPIO22 | OUT | I²C SCL | 同上 | 附录 21.1 ⭐ | 3.3V | 4.7kΩ 上拉 |
| GPIO23 | OUT | WS2812 DATA | J_WS → WS2812 | functional-spec B | 3.3V→5V | 经 BSS138 |
| GPIO25 | OUT | 舵机 PWM 1 | J_SV1 → 喂食舵机 | functional-spec B | 3.3V | 1kΩ 限流 |
| GPIO26 | OUT | 舵机 PWM 2 | J_SV2 → 遮阳舵机 | functional-spec B | 3.3V | 1kΩ 限流 |
| GPIO27 | OUT | PUMP_STOP | J_PUMP → 光耦 → 外部继电器 | ADR-0009 R-3 ⭐ | 3.3V | 高有效, 光耦隔离 |
| GPIO32 | IN | 数字输入 CH6 | J_DIN6 → 干接点 | ADR-0008 | 3.3V | 上拉+RC+钳位 |
| GPIO34 | IN | 脉冲输入 CH2 | J_DIN2 → YF-S201 流量 | ADR-0008 ⭐ | 3.3V | 5V 经 BSS138 |
| GPIO35 | IN | 脉冲输入 CH3 | J_DIN3 → 超声波 Echo | ADR-0008 ⭐ | 3.3V | 5V 经 BSS138 |
| GPIO36 | IN | 数字输入 CH4 | J_DIN4 → 干接点 | ADR-0008 | 3.3V | 上拉+RC+钳位 |
| GPIO39 | IN | 数字输入 CH5 | J_DIN5 → 干接点 | ADR-0008 | 3.3V | 上拉+RC+钳位 |

> ⭐ = 附录 21.1 明确指定的引脚, 不可更改

## 2. 避免使用的 GPIO

| GPIO | 原因 |
|------|------|
| GPIO0 | Strapping pin (boot 模式选择) |
| GPIO1 | UART0 TX (USB 调试) |
| GPIO2 | Strapping pin (boot 模式) |
| GPIO3 | UART0 RX (USB 调试) |
| GPIO6-11 | 连接 Flash, 绝对不可用 |
| GPIO12 | Strapping pin (Flash 电压选择) |
| GPIO15 | Strapping pin (boot 日志输出) |

## 3. I²C 地址分配

| 器件 | I²C 地址 | 引脚 | 位置 | 备注 |
|------|----------|------|------|------|
| MCP23017 | 0x20 | GPIO21/22 | 板载 | A0/A1/A2 → GND |
| INA226 | 0x40 | GPIO21/22 | 板载 | A0/A1 → GND, 测 12V 母线 |
| ADS1115 | 0x48 | GPIO21/22 | 板载 | ADDR → GND, pH/EC/浊度 |
| BH1750 | 0x23 | GPIO21/22 | 外接 (J_I2C) | 光照 |
| AHT20 | 0x38 | GPIO21/22 | 外接 (J_I2C) | 气温湿度 |
| BME280 | 0x76 | GPIO21/22 | 板载选贴 | 温湿压, SDO→GND |
| BMP280 | 0x77 | GPIO21/22 | 外接 (J_I2C) | 气压, SDO→VCC (避免与 BME280 冲突) |
| DS3231 | 0x68 | GPIO21/22 | 选贴 | RTC, 备用 |

## 4. MCP23017 端口分配

| 端口 | 引脚 | 功能 | 方向 | 备注 |
|------|------|------|------|------|
| GPA0 | 探头供电 CH1 (pH) | OUT | SI2302 控制 | 默认 LOW (断电) |
| GPA1 | 探头供电 CH2 (TDS) | OUT | SI2302 控制 | 默认 LOW (断电) |
| GPA2 | 探头供电 CH3 (浊度) | OUT | SI2302 控制 | 默认 LOW (断电) |
| GPA3 | 备用 | — | — | |
| GPA4 | 备用 | — | — | |
| GPA5 | 备用 | — | — | |
| GPA6 | 备用 | — | — | |
| GPA7 | 备用 | — | — | |
| GPB0-GPB7 | 备用 × 8 | — | — | 排针引出 |

## 5. 连接器引脚定义

### J_12V (12V 电源输入)
| Pin | 信号 |
|-----|------|
| 1 | +12V |
| 2 | GND |

### J_I2C (I²C 总线)
| Pin | 信号 |
|-----|------|
| 1 | +3.3V |
| 2 | GND |
| 3 | SDA (GPIO21) |
| 4 | SCL (GPIO22) |

### J_1W (1-Wire)
| Pin | 信号 |
|-----|------|
| 1 | +3.3V |
| 2 | GND |
| 3 | DATA (GPIO4) |

### J_DIN1-6 (数字/脉冲输入)
| Pin | 信号 | CH1 | CH2 | CH3 | CH4 | CH5 | CH6 |
|-----|------|-----|-----|-----|-----|-----|-----|
| 1 | SIGNAL | GPIO13 | GPIO34 | GPIO35 | GPIO36 | GPIO39 | GPIO32 |
| 2 | GND | — | — | — | — | — | — |

> CH2/CH3 为 5V 脉冲输入, 经 BSS138 电平转换。其余为 3.3V 干接点。

### J_MOS1-4 (12V MOSFET 输出)
| Pin | 信号 |
|-----|------|
| 1 | +12V |
| 2 | LOAD- (MOSFET DRAIN) |

### J_SV1-2 (舵机)
| Pin | 信号 |
|-----|------|
| 1 | +5V |
| 2 | GND |
| 3 | PWM (GPIO25/GPIO26) |

### J_WS (WS2812)
| Pin | 信号 |
|-----|------|
| 1 | +5V |
| 2 | GND |
| 3 | DATA (GPIO23, 经电平转换) |

### J_PZEM (PZEM UART)
| Pin | 信号 |
|-----|------|
| 1 | +5V |
| 2 | GND |
| 3 | TX (GPIO17 → PZEM RX) |
| 4 | RX (GPIO16 ← PZEM TX) |

### J_PUMP (泵控制输出, 光耦隔离)
| Pin | 信号 | 默认 |
|-----|------|------|
| 1 | COM (光耦集电极) | — |
| 2 | NO (常开, 默认) | 泵关 ⭐ |
| 3 | NC (常闭, 需验收后启用) | 未连接 |

> 跳线 JP_NCNO: 默认短接 NO 侧 (泵 OFF)。翻 NC 需 MVP-2/3 门禁验收。

### J_HW (高水位浮球)
| Pin | 信号 |
|-----|------|
| 1 | FLOAT_NC (+12V 侧) |
| 2 | FLOAT_COM (光耦侧) |

### J_PRB (探头供电)
| Pin | 信号 |
|-----|------|
| 1 | V_PROBE1 (pH, GPA0 控制) |
| 2 | GND |
| 3 | V_PROBE2 (TDS, GPA1 控制) |
| 4 | GND |
| 5 | V_PROBE3 (浊度, GPA2 控制) |
| 6 | GND |
