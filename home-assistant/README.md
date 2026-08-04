# home-assistant · 中枢配置

Home Assistant 是 L2 中枢：跨模块自动化、告警、仪表盘。节点数据经 MQTT（`aqua/<node>/<metric>`）进入。

## 目录

- `packages/` — 按功能拆分的包（自动化、告警、辅助实体）。用 `packages: !include_dir_named packages/` 挂载。

## 计划中的自动化（Phase 3）

- **失效告警**（最优先）：泵停 / 流量 0 / 缺水 / 高温 → 手机推送。
- **高温降温级联**：>30℃ 开风扇 → >32℃ 加遮阳+打氧 → >34℃ 提醒人工。
- **太阳能优先调度**：白天跑重负载，电池低只保命。
- **天气联动**：拉广州天气，热浪前预降温、台风预警提醒。

## 约定

- 敏感信息放 HA 的 `secrets.yaml`（不提交）。
- 仪表盘 YAML 导出放 `../data/grafana/` 或此处 `dashboards/`。

TODO：MVP-4 上线后提交第一个「失效告警」包。
