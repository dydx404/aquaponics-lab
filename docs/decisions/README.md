# 架构决策记录 ADR

记录**重大且不易逆转**的决定：背景、选择、理由、后果。新决定复制下面模板，编号递增。

## 索引

- [0001 · 采用 CHOP2 单泵闭环](0001-chop2-single-pump.md)
- [0002 · 多口小玻璃缸「实验鱼房」而非单一大缸](0002-multi-small-glass-tanks.md)
- [0003 · 重物落地：弱层板下的载荷布局](0003-heavy-tanks-on-floor.md)
- [0004 · 供电分域：220V 市电泵 + 12V DC 控制系统](0004-power-domains.md)
- [0005 · 接口契约分层：电气冻结 / 物理连接器延后](0005-connector-layer-deferred.md)
- [0006 · I²C 只在盒内；对外线缆的缓冲/线材/最大长度](0006-i2c-cable-limits.md)
- [0007 · 传感轨 3.3V + 电平转换责任方（底板）+ 连接器防误插](0007-sensor-rail-and-level-translation.md)
- [0008 · 节点 I/O 供给：数字输入/脉冲/专用 header + GPIO 预算](0008-node-io-provisioning.md)
- [0009 · 泵计量、控制信号与失电默认态](0009-pump-metering-and-control.md)
- [0010 · 市电安全接地（货架 PE + 接地探针 + 单点接地）](0010-mains-safety-bonding.md)

## 模板

```markdown
# ADR-XXXX · 标题

- 状态：提议 / 已采纳 / 已废弃 / 被 ADR-YYYY 取代
- 日期：YYYY-MM-DD

## 背景
面临什么问题、约束是什么。

## 决定
选择了什么。

## 理由
为什么这样选，比较过哪些方案。

## 后果
带来的好处、代价、后续要注意的点。
```
