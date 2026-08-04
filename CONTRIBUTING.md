# 贡献指南 · Contributing

感谢参与 `aquaponics-lab`！这是一个开源硬件 + 固件 + 文档项目，欢迎从任何一个方向切入。

## 快速上手

1. Fork & clone。
2. 从 `main` 切一个分支：`feat/xxx`、`fix/xxx`、`docs/xxx`、`hw/xxx`。
3. 提交（见下方规范），发 PR，关联对应的 Issue / MVP 里程碑。

## 分支与提交规范

- 分支命名：`<type>/<short-desc>`，如 `feat/tank-node-ph`。
- 提交信息用 **Conventional Commits**：
  - `feat:` 新功能 · `fix:` 修复 · `docs:` 文档 · `hw:` 硬件 · `chore:` 杂项 · `refactor:` 重构
  - 例：`feat(esphome): add DS18B20 water-temp sensor to tank node`
- 一个 PR 只做一件事，尽量小而清晰。

## 命名标准（重要 · 保证可协作）

- **节点名**：`node-<function><index>`，如 `node-tank01`、`node-power`、`node-grow`、`node-vision`。
- **MQTT 主题**：`aqua/<node>/<metric>`，如 `aqua/tank01/water_temp`、`aqua/power/battery_v`。
- **文件/目录**：kebab-case（全小写连字符）。
- **文档**：中文为主，关键处加英文；每个 MVP 一篇 build 文档并写明**验收标准**。

## 硬件与文档

- 硬件改动要更新 [`docs/03-bom/`](docs/03-bom/) 和 [`hardware/`](hardware/) 的接线图。
- 3D 打印件：**源文件**（`.f3d` / `.scad` / `.step`）放 `hardware/3d-models/src/`，导出的 **STL** 放 `stl/`。
- 重大设计决定请写一条 **ADR**：见 [`docs/decisions/`](docs/decisions/)。

## 安全底线（不接受违反的 PR）

- 涉及市电（220V）必须走漏电保护，配置/文档需体现。
- 任何"让电子系统正常"成为鱼存活前提的设计，必须同时给出**物理失效安全**兜底。

## 不要提交

- 任何 `secrets.yaml`、WiFi/MQTT 密码、密钥、家庭住址、可定位的个人信息。用 `secrets.example.yaml` 占位。
