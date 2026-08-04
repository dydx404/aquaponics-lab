# 第 9 章 · 控制节点与固件（M6）

> 演进中。负责人：系统/软件。节点是连接物理世界与数字世界的边缘。

## 9.1 职责与边界

- **职责**：在边缘采集传感、驱动执行、上报 MQTT、执行本地兜底逻辑。
- **原则**：节点只做**本模块**的事与**保命兜底**；跨模块智能放中枢。
- **接口**：MQTT 主题、引脚定义、OTA（见 [第 13 章](13-interfaces.md)）。

## 9.2 为什么一模块一节点（分布式）⭐

- **物理就近**：传感/执行靠近对象，减少长线干扰。
- **故障隔离**：一个节点挂了，只影响一个模块。
- **可热插拔**：加模块 = 加一个 ESP32 + 配置，符合铁律二。
- **并行开发**：不同人可各自开发不同节点。

节点命名：`node-<function><index>`，如 `node-tank01`、`node-power`、`node-grow`、`node-vision`。

## 9.3 ESP32 平台 🔬

- 双核 Xtensa，集成 WiFi/BLE，多路 GPIO、ADC、I²C/SPI、硬件 PWM（LEDC）。
- **注意**：内置 ADC 非线性且噪声大 → 模拟水质走外置 ADS1115；部分 GPIO 有上电约束（strapping pins），接线避坑（见附录）。
- 变体：ESP32-S3 带更多 RAM/AI 指令与摄像头支持，用于 `node-vision`。

## 9.4 ESPHome：声明式固件 ⭐

本项目固件统一用 **ESPHome**：用 YAML 声明传感器/执行器，自动生成固件，支持 **OTA** 与 Home Assistant/MQTT 原生集成。

优点：
- 声明式、可读、可复用（`packages:`）。
- OTA 升级，无需插线。
- 改一行 YAML 即加一个传感器。

结构（见 [`firmware/esphome/`](../../firmware/esphome/)）：

```
firmware/esphome/
├─ common/base.yaml       # 复用底座：wifi / mqtt / ota / 时间
├─ node-tank01.yaml       # 具体节点（引入 base + 本节点传感/执行）
└─ secrets.example.yaml   # 密钥模板（真值放 secrets.yaml，不提交）
```

`node-tank01` 示例（MVP-4）：水温(DS18B20) + 缺水(浮球) + 泵电流(INA219)，发布到 `aqua/tank01/*`。

## 9.5 固件设计规范

- **复用**：wifi/mqtt/ota/时间等放 `common/base.yaml`，各节点 `packages:` 引入。
- **命名**：MQTT `topic_prefix: aqua/${node_name}`；实体名清晰、稳定。
- **引脚**：每个 node 的 YAML 顶部注释写引脚分配，与 [第 21 章附录](21-appendix-pinouts.md) 和接线图一致。
- **密钥**：一律 `!secret`，`secrets.yaml` 进 `.gitignore`（公开仓库红线）。

## 9.6 本地兜底与鲁棒性（呼应铁律一）⚠️

即使中枢/网络失效，节点也要"不添乱、能保命"：

- **看门狗**：ESPHome 内置，卡死自动重启。
- **本地保命逻辑**：可在节点内置最低限度规则（如"缺水浮球触发 → 本地停泵"），不依赖 HA。
- **失联指示**：断 WiFi/MQTT 时本地状态灯/日志可查；恢复后自动重连。
- **坏值防护**：传感器超量程判故障，不上报误导性数据。

## 9.7 开发与烧录流程

```bash
pip install esphome            # 或 pipx
cp secrets.example.yaml secrets.yaml   # 填 wifi/mqtt
esphome run node-tank01.yaml           # 首刷走 USB，之后 OTA
```

## 9.8 TODO

- [ ] `node-tank01` 上线并接入 HA（MVP-4）。
- [ ] `node-power`、`node-grow`、`node-vision` 骨架。
- [ ] 节点本地保命逻辑规范。
