# scripts · 工具脚本

放刷机、备份、数据导出、CI 校验等小工具。

## 目录

```
scripts/
├── simulator/              — MQTT 传感器模拟器（Python）
│   ├── aquaponics_sim/     — 模拟器核心模块
│   ├── run.py              — 入口脚本
│   ├── config.example.yaml — 配置示例
│   └── requirements.txt
├── validate-mqtt-topics.py — MQTT 主题命名校验（CI）
└── validate-yaml.py         — YAML 语法校验（CI）
```

## MQTT 传感器模拟器

见 [simulator/README.md](simulator/README.md)。

**快速启动：**
```bash
cd simulator
pip install -r requirements.txt
python run.py
```

## CI 校验工具

### validate-yaml.py

检查所有 YAML 文件能否正确解析：

```bash
python scripts/validate-yaml.py
# 或指定路径
python scripts/validate-yaml.py home-assistant firmware/esphome
```

### validate-mqtt-topics.py

检查 HA 配置中的 MQTT 主题是否符合 `aqua/<node>/<metric>` 契约：

```bash
python scripts/validate-mqtt-topics.py
# 或指定 HA 目录
python scripts/validate-mqtt-topics.py path/to/home-assistant
```

## 规划中

- `flash.sh` — 一键 `esphome run` 指定节点。
- `ha-backup.sh` — 备份 Home Assistant 配置与包。

保持脚本跨平台友好（POSIX sh / PowerShell 各份或注明用法）。
