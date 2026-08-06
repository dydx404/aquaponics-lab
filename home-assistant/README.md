# home-assistant · 中枢配置

Home Assistant 是 L2 中枢：跨模块自动化、告警、仪表盘。节点数据经 MQTT（`aqua/<node>/<metric>`）进入。

## 目录

- `packages/` — 按功能拆分的包。用 `packages: !include_dir_named packages/` 挂载。

## 安装

1. 在 HA 的 `configuration.yaml` 中添加：

```yaml
mqtt:
  broker: localhost      # or your MQTT broker IP
  port: 1883

packages: !include_dir_named packages/
```

2. 将 `packages/` 目录中的 YAML 文件复制到 HA 配置目录下的 `packages/` 文件夹。

3. 重启 Home Assistant 或调用 `reload` 服务。

## 配置包

### aqua_sensors.yaml — MQTT 传感器实体

| 实体 | 主题 | 类型 | 单位 |
|------|------|------|------|
| Tank01 Water Temperature | `aqua/tank01/water_temp` | sensor | °C |
| Tank01 pH | `aqua/tank01/ph` | sensor | pH |
| Tank01 Ammonia | `aqua/tank01/ammonia` | sensor | mg/L |
| Tank01 Nitrite | `aqua/tank01/nitrite` | sensor | mg/L |
| Tank01 Nitrate | `aqua/tank01/nitrate` | sensor | mg/L |
| Tank01 Pump Current | `aqua/tank01/pump_current` | sensor | A |
| Tank01 Flow Rate | `aqua/tank01/flow` | sensor | L/min |
| Tank01 Battery Voltage | `aqua/tank01/battery_v` | sensor | V |
| Tank01 Solar Current | `aqua/tank01/solar_current` | sensor | A |
| Tank01 Low Water | `aqua/tank01/low_water` | binary_sensor | ON/OFF |
| Tank01 Online | `aqua/tank01/status` | binary_sensor | online/offline |

另含两个 template sensor：
- **Nitrogen Cycle Stage** — 根据氨/亚硝酸/硝酸盐值自动判断：Ammonia Spike → Nitrite Rising → Nitrite Peak → Cycled
- **Pump Status** — 综合电流和流量判断：Running / Stopped / Blocked / No Flow

### aqua_alarms.yaml — 失效告警

| 告警 | 触发条件 | 清除条件 | 延时 |
|------|----------|----------|------|
| Pump Stopped | pump_current < 0.05A | pump_current > 0.05A | 30s 触发 / 10s 清除 |
| No Flow | flow < 0.5 L/min | flow > 0.5 L/min | 30s 触发 / 10s 清除 |
| Low Water | low_water = ON | low_water = OFF | 即时触发 / 10s 清除 |
| High Temp | water_temp > 32°C | water_temp < 30°C | 30s 触发 / 60s 清除 |
| Node Offline | status = offline | status = online | 60s 触发 / 即时清除 |

设计要点：
- **迟滞**：高温告警 2°C 迟滞带（32°C 触发，30°C 清除），防止震荡
- **联锁**：泵停时抑制"无流量"告警（根因已识别，避免重复告警）
- **重复提醒**：每 5 分钟检查活跃告警并重新推送通知
- **input_boolean** 状态跟踪：每个告警有独立状态位，可在 HA Lovelace 中展示

### aqua_cooling.yaml — 高温降温级联

| 级别 | 触发温度 | 动作 | 清除温度 |
|------|----------|------|----------|
| L1 | ≥30°C | 风扇 ON | <28°C |
| L2 | ≥32°C | + 遮阳 + 打氧 | <30°C |
| L3 | ≥34°C | + 人工告警 | <32°C |

设计要点：
- **2°C 迟滞带**：每级触发和清除温差 2°C，防止执行器频繁切换
- **级联联锁**：L2 激活时确保 L1 也激活；L1 清除时检查 L2 是否仍在激活
- **反向关停**：降温时 L3 → L2 → L1 逐级清除，避免突变
- **MQTT 命令**：通过 `aqua/tank01/<actuator>/set` 控制风扇、遮阳、打氧

## 本地验证

```bash
# 1. 启动 MQTT broker
docker run -d --name mosquitto -p 1883:1883 eclipse-mosquitto

# 2. 启动模拟器（会发布 aqua/tank01/* 遥测）
cd ../scripts/simulator
python run.py

# 3. 在 HA 中观察传感器实体出现
# 4. 注入故障测试告警：
python run.py --fault pump_fail:tank01     # 泵停告警
python run.py --fault high_temp:tank01     # 高温 + 降温级联
python run.py --fault low_water:tank01     # 缺水告警
```

## 约定

- 敏感信息放 HA 的 `secrets.yaml`（不提交）。
- 仪表盘 JSON 导出放 `../data/grafana/`。
- 多节点：复制 YAML 并将 `tank01` 替换为新节点 ID。
