# aquaponics-lab 🐟 🌿 ⚡

> 一个可复刻、模块化、可持续迭代的**家庭智能鱼菜共生生态实验平台**。
> 工业风、开源硬件，跑在 **Home Assistant + ESPHome + MQTT** 之上。

**English abstract** — `aquaponics-lab` is an open-source, modular, reproducible smart
aquaponics platform for a home balcony. It treats aquaponics as a living "eco-SCADA"
lab: multiple small glass tanks on a **single-pump CHOP2 loop**, instrumented with
ESP32 / ESPHome nodes, water-quality probes and computer vision, all orchestrated by
Home Assistant over MQTT. The design favors **engineering aesthetics, hackability and
long-term iteration over yield**. Docs are Chinese-first with English summaries.

📍 场景：广州 · 东南朝向小阳台 · 单泵闭环 · 12V DC + 太阳能
🚧 状态：早期建设中（MVP-1 骨架）

---

## ✨ 特点

- **单泵 CHOP2 闭环**：全系统只有一个水泵，其余靠重力；断电断网也不翻缸（物理失效安全优先）。
- **多小玻璃缸「实验鱼房」**：每口缸 = 一个可热插拔的实验单元，可做 A/B 对照，而不是一口大缸。
- **分布式节点**：一个模块一个 ESP32（ESPHome），统一 MQTT 主题命名，接上即在 HA 出现。
- **数据即乐趣**：Grafana 记录氮循环 / 水质 / 能量曲线；Frigate + 摄像头做鱼行为视觉。
- **离网就绪**：12V DC 母线 + 太阳能，能量调度可视化。
- **为复刻而生**：BOM、接线图、ESPHome 配置、3D 打印件全开源。

## 🧭 系统架构

见 [`docs/00-overview.md`](docs/00-overview.md)。一句话：

```
集水/生化桶(单泵) → 泵上顶 → 各玻璃缸(供水总管+球阀) → 缸口溢流
        → 底部回水总管 → 回集水桶   ‖   ESP32 节点 → MQTT → Home Assistant
```

## 🚀 快速开始（给复刻者）

1. 读 [`docs/00-overview.md`](docs/00-overview.md) 理解系统与设计取舍。
2. 按 [`docs/03-bom/`](docs/03-bom/) 备料。
3. 按 [`docs/02-build/`](docs/02-build/) 的 **MVP 顺序**一步步搭（每步有验收标准）。
4. 刷 [`firmware/esphome/`](firmware/esphome/) 的节点固件（先复制 `secrets.example.yaml` → `secrets.yaml`）。
5. 导入 [`home-assistant/`](home-assistant/) 的配置，接入 MQTT。

### 🧪 纯软件快速体验（无需硬件）

不想等硬件到手？有两种方式跑起来：

#### 方式一：Docker Compose 一键全栈（推荐）

```bash
cd deploy/
cp .env.example .env       # 编辑密码
docker compose up -d       # 一条命令拉起全栈
```

启动后：
- **Grafana** → http://localhost:3000（仪表盘自动加载，数据在动）
- **Home Assistant** → http://localhost:8123（传感器实体 + 自动化）
- 模拟器每 5s 发布全量遥测，Grafana 实时刷新

详见 [`deploy/README.md`](deploy/README.md)。

#### 方式二：手动启动模拟器

```bash
# 1. 启动 MQTT broker
docker run -d --name mosquitto -p 1883:1883 eclipse-mosquitto

# 2. 启动传感器模拟器
cd scripts/simulator
pip install -r requirements.txt
python run.py                              # 默认参数
python run.py --fault pump_fail:tank01    # 注入泵故障，测试告警
python run.py --fault high_temp:*         # 注入高温，测试降温级联

# 3. 导入 HA 配置包 → 传感器实体自动出现 → 告警触发
# 4. 导入 Grafana 仪表盘 JSON → 实时曲线
```

## 📂 目录结构

| 路径 | 内容 |
|---|---|
| `docs/` | 设计、施工、BOM、运维、架构决策记录（ADR） |
| `firmware/esphome/` | 各 ESP32 节点的 ESPHome 配置 |
| `home-assistant/` | HA 配置包：传感器实体、失效告警、降温级联自动化 |
| `hardware/` | 接线图、原理图、3D 打印件（源文件 + STL） |
| `data/grafana/` | Grafana 仪表盘 JSON（氮循环、水质、养分、环境、能量、泵流量） |
| `scripts/simulator/` | MQTT 传感器模拟器（Python，无需硬件即可开发调试） |
| `scripts/` | CI 校验工具（YAML 语法、MQTT 主题命名） |
| `deploy/` | Docker Compose 全栈部署（Mosquitto + InfluxDB + Grafana + HA + 模拟器） |

## 🗺 路线图（MVP）

| 阶段 | 目标 | 验收 |
|---|---|---|
| MVP-0 | 场地与图纸 | ✅ 尺寸/朝向/排水已定 |
| MVP-1 | 骨架 | 货架立稳、空缸就位 |
| MVP-2 | 水路闭环 | 连跑 24h 零漏水 |
| MVP-3 | 钟形虹吸 / 溢流 | 稳定循环 24h |
| MVP-4 | 首个 ESP32 节点 | 水温+水位+泵流上 HA、断泵告警 |
| MVP-5 | 养菌开缸 | 氨/亚硝酸归零、出现硝酸盐 |
| MVP-6 | 放鱼 | 稳定运行 1 周 |

之后：自动化 → 太阳能离网 → 视觉/AI → 闭合物质循环。详见 [`docs/02-build/`](docs/02-build/)。

## 🤝 贡献

欢迎协作，先读 [`CONTRIBUTING.md`](CONTRIBUTING.md)。用 Issue 讨论、PR 提交、Conventional Commits。

## 📜 许可

- **代码 / 固件**：[MIT](LICENSE)
- **文档 / 硬件设计 / 媒体**：[CC-BY-SA-4.0](docs/LICENSE)

## ⚠️ 免责声明

涉及活体动物、水电共存与高温环境。请自行确保用电安全（漏电保护）、结构承重与动物福利。
本项目按「现状」提供，作者不对任何损失负责。
