# 《aquaponics-lab 项目手册》Project Handbook

> 一本可复刻的家庭智能鱼菜共生生态实验平台的**完整工程手册**。
> 覆盖：愿景 → 系统架构 → 各模块原理 → 接口契约 → 分工 → 协作流程 → 测试 → 运维 → 安全 → 附录。
> 面向：项目发起者、硬件协作者（EE）、未来贡献者与任何想复刻的人。

**版本**：v0.1（草稿）· **最后更新**：2026-08-05 · **许可**：CC-BY-SA-4.0（文档）/ MIT（代码）

---

## 这本手册怎么用

- **稳定的东西写进书**：愿景、架构、模块原理、**接口契约**、安全底线——这些不常变，是"宪法"。
- **易变的细节指向 living docs**：具体施工步骤看 [`../02-build/`](../02-build/)，决策看 [`../decisions/`](../decisions/)，配置看 [`../../firmware/`](../../firmware/)。手册**只引用不复制**，避免过期。
- **新人第一天**：读 [第 1–3 章] 了解全局 → 读 [第 13 章 接口契约] + [第 14 章 分工] 知道自己该干嘛、怎么对接 → 读 [第 15 章 工作流] 知道怎么提交。

## 目录 Table of Contents

### 第一部分 · 项目
- [第 1 章 · 前言与如何使用本手册](01-preface.md)
- [第 2 章 · 愿景、目标与设计原则](02-vision-and-principles.md)
- [第 3 章 · 系统架构总览](03-architecture.md)

### 第二部分 · 模块与原理（工程核心）
- [第 4 章 · 水循环与流体系统](04-hydraulics.md)
- [第 5 章 · 结构与机械](05-mechanical.md)
- [第 6 章 · 供电与能源系统](06-power.md)
- [第 7 章 · 传感器与测量原理](07-sensors.md)
- [第 8 章 · 执行器与驱动电路](08-actuators.md)
- [第 9 章 · 控制节点与固件](09-firmware.md)
- [第 10 章 · 中枢、网络与自动化](10-hub-and-automation.md)
- [第 11 章 · 数据、可视化与智能](11-data-and-ai.md)
- [第 12 章 · 生态与生物系统](12-biology.md)

### 第三部分 · 工程与协作
- [第 13 章 · 接口契约](13-interfaces.md) ⭐ 并行开发的关键
- [第 14 章 · 分工与责任](14-division-of-labor.md)
- [第 15 章 · 协作工作流](15-workflow.md)
- [第 16 章 · 测试、调试与验收](16-testing.md)
- [第 17 章 · 运维与维护](17-operations.md)
- [第 18 章 · 风险与安全](18-risk-and-safety.md)

### 第四部分 · 路线图与附录
- [第 19 章 · 路线图与里程碑](19-roadmap.md)
- [第 20 章 · 物料清单 BOM](20-bom.md)
- [第 21 章 · 附录：引脚 / 接线 / 地址表](21-appendix-pinouts.md)
- [第 22 章 · 术语表](22-glossary.md)
- [第 23 章 · 参考资料](23-references.md)

## 如何生成 PDF

本手册用 Markdown 编写，可用 [pandoc](https://pandoc.org/) 合并导出为一本带目录的 PDF：

```bash
# 需要 pandoc + 一个 LaTeX 引擎(xelatex, 支持中文)
cd docs/handbook
pandoc README.md $(ls [0-9]*.md | sort) \
  -o aquaponics-lab-handbook.pdf \
  --toc --toc-depth=2 --number-sections \
  -V CJKmainfont="Noto Sans CJK SC" -V geometry:margin=2.5cm --pdf-engine=xelatex
```

也可用仓库脚本 `scripts/build-handbook.sh`（规划中）。
