# 第 15 章 · 协作工作流

> 稳定。规矩定清楚，协作才顺。核心：feature branch + PR 互审 + CI + ADR。

## 15.1 分支模型 🌿

- `main`：**受保护**，始终可用/可复刻。不直接 push。
- 特性分支：`<type>/<short-desc>`
  - `feat/` 新功能，`fix/` 修复，`docs/` 文档，`hw/` 硬件，`chore/` 杂项，`refactor/` 重构。
  - 例：`feat/tank01-ph-sensor`、`hw/power-bus-schematic`、`docs/handbook-ch7`。
- 一个分支一件事，尽量小、易审。

```
main ──o───────o──────────o──►
        \      /            \
   feat/x o──o(PR)      hw/y o──o(PR)
```

## 15.2 日常流程

```bash
git switch main && git pull
git switch -c feat/xxx
# ... 改动 + 提交（见提交规范）...
git push -u origin feat/xxx
# 在 GitHub 开 PR → 对方 review → CI 绿 → 合并（squash）
```

## 15.3 提交规范（Conventional Commits）

`<type>(<scope>): <描述>`，例：
- `feat(esphome): add DS18B20 water-temp to tank01`
- `hw(power): add flyback diode to pump driver`
- `docs(handbook): write ch13 interface contracts`

好处：可读、可自动生成 CHANGELOG、便于回溯。

## 15.4 Pull Request 规范

- 用 PR 模板；关联 Issue（`Closes #`）。
- **互审**：硬件的 PR 由软件粗审接口，软件的 PR 由硬件粗审引脚/电气假设；关键改动都要一次 review。
- 合并前 **CI 必须绿**（secrets 守卫 + lint）。
- PR 检查清单（见模板）：命名规范、无 secrets、安全考量、更新文档/BOM/接线图、重大变更有 ADR。

## 15.5 CI（持续集成）

`.github/workflows/ci.yml`：
- **guard-secrets**：确保没有 `secrets.yaml` 被提交（公开仓库红线）。
- **yamllint**：宽松风格检查。
- 后续可加：ESPHome 配置编译校验、markdown 链接检查。

## 15.6 ADR（架构决策记录）

**重大且不易逆转**的决定写 ADR（[docs/decisions](../decisions/)）：背景/决定/理由/后果。已有 0001（CHOP2）、0002（多小缸）、0003（重物落地）。接口变更**必须**配 ADR。

## 15.7 版本与发布

- **语义化版本(SemVer)** `主.次.修`；用 git tag 标记。
- 变更记入 `CHANGELOG.md`（Keep a Changelog）。
- 里程碑（milestones）对应 MVP；发布时把 `Unreleased` 归入版本号。

## 15.8 Issue 与看板

- **施工进度**：用 `build-log` Issue 模板，按 MVP 记录进度/照片/数据/问题。
- **Bug**：用 `bug_report` 模板。
- 用 **GitHub Projects 看板** + milestones 管理"一步步"推进。

## 15.9 安全红线（CI/评审拦截）

- 不提交 secrets/密码/密钥/住址/可定位个人信息。
- 涉市电必含漏电保护；涉活体必含失效安全。
