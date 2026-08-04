# firmware · ESPHome 节点

每个物理模块 = 一个 ESP32 节点，跑 ESPHome，通过 MQTT（主题 `aqua/<node>/<metric>`）接入 Home Assistant。

## 目录

- `common/base.yaml` — 所有节点复用的底座（wifi / mqtt / ota / 时间）。
- `node-tank01.yaml` — MVP-4 首个传感节点（水温 + 水位 + 泵电流）。
- `secrets.example.yaml` — 密钥模板。**复制成 `secrets.yaml`（已 gitignore）并填写，切勿提交。**

## 快速开始

```bash
# 安装（任选其一）
pipx install esphome        # 或  pip install esphome

# 准备密钥
cp secrets.example.yaml secrets.yaml   # 然后填入 wifi / mqtt

# 编译并首刷（USB），之后可 OTA
esphome run node-tank01.yaml
```

## 命名规范

- 节点：`node-<function><index>`（`node-tank01`、`node-power`、`node-grow`、`node-vision`）。
- MQTT：`aqua/<node>/<metric>`（由 `mqtt.topic_prefix: aqua/${node_name}` + 实体名生成）。

## 约定

- 传感/执行在节点本地；**跨模块逻辑与告警放 Home Assistant**（见 `../../home-assistant/`）。
- 引脚以各节点 yaml 顶部注释为准；接线图见 `../../hardware/electronics/`。
