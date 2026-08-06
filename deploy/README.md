# aquaponics-lab · Docker Compose 全栈部署

> 一条 `docker compose up -d` 拉起完整软件栈：MQTT broker + 时序数据库 + 可视化 + HA + 模拟器。

## 前置要求

- Docker 20.10+
- Docker Compose v2
- 磁盘空间 ~2 GB（镜像 + 数据）

## 快速开始

```bash
cd deploy/

# 1. 复制环境配置
cp .env.example .env
#    编辑 .env，把密码改成你自己的

# 2. 一键启动全栈
docker compose up -d

# 3. 等待 ~30s 让所有服务就绪
docker compose logs -f simulator   # 看到模拟器在发数据 = OK
```

启动后访问：

| 服务 | 地址 | 默认账号 |
|---|---|---|
| Grafana | http://localhost:3000 | admin / （.env 里的密码） |
| Home Assistant | http://localhost:8123 | 首次访问设置 |
| InfluxDB | http://localhost:8086 | aqua / （.env 里的密码） |
| Mosquitto MQTT | localhost:1883 | 无认证（本地） |

Grafana 打开后 → 左侧 **Dashboards** → **Aquaponics** 文件夹 → **Aquaponics Lab Overview** 仪表盘已自动加载，数据在动。

## 服务架构

```
simulator ──MQTT──▶ mosquitto ──▶ telegraf ──▶ influxdb ──▶ grafana
                        │
                        └──▶ home-assistant (传感器实体 + 自动化)
```

| 服务 | 镜像 | 作用 |
|---|---|---|
| mosquitto | eclipse-mosquitto:2 | MQTT broker，所有节点通信枢纽 |
| telegraf | telegraf:latest | MQTT→InfluxDB 桥接，订阅 `aqua/+/+` 写入时序库 |
| influxdb | influxdb:1.8 | 时序数据库，90 天保留策略 |
| grafana | grafana/grafana:latest | 可视化，provisioning 自动加载数据源 + 仪表盘 |
| home-assistant | ghcr.io/home-assistant/home-assistant:stable | 传感器实体、告警自动化、P2 控制 |
| simulator | 本地构建 | Python 模拟器，每 5s 发布全量遥测 + 响应执行器命令 |

## 配置说明

### 环境变量 (.env)

| 变量 | 默认值 | 说明 |
|---|---|---|
| `TZ` | Asia/Shanghai | 时区 |
| `MOSQUITTO_PORT` | 1883 | MQTT broker 端口 |
| `INFLUXDB_PORT` | 8086 | InfluxDB HTTP 端口 |
| `GRAFANA_PORT` | 3000 | Grafana 端口 |
| `HA_PORT` | 8123 | Home Assistant 端口 |
| `INFLUXDB_DATABASE` | aqua | 数据库名 |
| `INFLUXDB_USER` | aqua | 数据库用户 |
| `INFLUXDB_PASSWORD` | changeme_influx | **必须修改** |
| `GRAFANA_USER` | admin | Grafana 管理员 |
| `GRAFANA_PASSWORD` | changeme_grafana | **必须修改** |
| `SIM_INTERVAL` | 5 | 模拟器发布间隔（秒） |
| `SIM_TIME_SCALE` | 1.0 | 氮循环时间倍率（>1 加速演示） |

### Grafana 数据源 & 仪表盘

- 数据源：自动 provisioning（`grafana/provisioning/datasources/influxdb.yml`）
- 仪表盘：自动从 `data/grafana/*.json` 加载
- 仪表盘里的 `$node` 变量自动从 InfluxDB tag 列表填充

### Home Assistant 包

HA 配置从 `home-assistant/` 目录加载，packages 从项目根的 `home-assistant/packages/` 只读挂载：

- `aqua_sensors.yaml` — 全量传感器实体 + 执行器开关
- `aqua_alarms.yaml` — 失效告警（泵停/缺水/高温/离线）
- `aqua_cooling.yaml` — 三级降温级联
- `aqua_automations.yaml` — P2 自动化（喂食/光周期/补水）

### Telegraf MQTT→InfluxDB 映射

Telegraf 订阅 `aqua/+/+` 和 `aqua/+/+/state`，将 MQTT topic 直接映射为 InfluxDB measurement：

```
aqua/tank01/water_temp  →  measurement: "aqua.tank01.water_temp"
aqua/tank01/feeder/state →  measurement: "aqua.tank01.feeder.state"
```

Grafana 查询使用 `SELECT mean("value") FROM "aqua".."aqua.$node.<metric>"` 格式。

## 常用命令

```bash
# 查看所有服务状态
docker compose ps

# 查看某个服务日志
docker compose logs -f simulator
docker compose logs -f home-assistant

# 停止全栈
docker compose down

# 停止并删除数据卷（完全重置）
docker compose down -v

# 重新构建模拟器（代码改了之后）
docker compose build simulator && docker compose up -d simulator

# 手动发一条 MQTT 命令（测试执行器）
docker compose exec mosquitto mosquitto_pub -t aqua/tank01/feeder/set -m ON
docker compose exec mosquitto mosquitto_pub -t aqua/tank01/light/set -m ON
docker compose exec mosquitto mosquitto_pub -t aqua/tank01/refill/set -m ON
```

## 故障排查

### Grafana 面板没数据

1. 检查模拟器是否在运行：`docker compose logs simulator`
2. 检查 Telegraf 是否在写入：`docker compose logs telegraf`
3. 检查 InfluxDB 是否有数据：
   ```bash
   docker compose exec influxdb influx -database aqua -username aqua -password $INFLUXDB_PASSWORD -execute 'SHOW MEASUREMENTS LIMIT 10'
   ```
4. 检查 Grafana 数据源是否配置成功：Settings → Data Sources → InfluxDB → Save & Test

### Home Assistant 实体不出现

1. 检查 HA 是否连上 MQTT：Settings → Devices & Services → MQTT
2. 检查 packages 是否加载：Settings → YAML → Reload Packages
3. 查看 HA 日志：`docker compose logs home-assistant | grep -i mqtt`

### 端口冲突

修改 `.env` 中的端口映射，例如：
```
MOSQUITTO_PORT=1884
GRAFANA_PORT=3001
```

## 安全提醒

- **生产环境**请给 Mosquitto 加认证（修改 `mosquitto.conf`，设 `allow_anonymous false`）。
- **不要提交 `.env`** — 它包含密码，已在 `.gitignore` 中排除。
- HA 首次访问时设置自己的管理员密码。
