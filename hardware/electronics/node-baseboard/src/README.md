# src/ — node-baseboard 工程源文件

## 文件说明

| 文件 | 说明 |
|------|------|
| `generate_netlist.py` | SKiDL Python 脚本, 生成 KiCad 网表 (.net) |

## 使用方法

### 方式 1: SKiDL 生成网表 (推荐)

```bash
# 1. 安装 KiCad (提供符号库)
#    Windows: https://www.kicad.org/download/
#    Linux: sudo apt install kicad

# 2. 安装 SKiDL
pip install skidl

# 3. 设置符号库路径 (按实际安装路径调整)
export KICAD_SYMBOL_DIR="/usr/share/kicad/symbols"  # Linux
# Windows (Git Bash):
# export KICAD_SYMBOL_DIR="C:/Program Files/KiCad/share/kicad/symbols"

# 4. 生成网表
cd hardware/electronics/node-baseboard/src
python generate_netlist.py

# 5. 导入 KiCad
#    KiCad → File → Import → Netlist → 选 node-baseboard.net
#    然后布局 PCB

# 6. 导入嘉立创EDA
#    嘉立创EDA → 文件 → 导入 → KiCad 网表
```

### 方式 2: 手动画原理图

按 `DESIGN.md` 的电路描述, 在 KiCad 或嘉立创EDA 中手动绘制原理图。
BOM 中的 LCSC 型号可直接在嘉立创EDA 中搜索对应元件封装。

## 下一步 (PCB 布板)

1. 用生成的网表或手绘原理图, 在 EDA 工具中进行 PCB 布局
2. 遵守 `DESIGN.md §18` 的 PCB 设计约束
3. 布板完成后导出 Gerber + 3D 预览截图 + DRC 报告
4. 提交给 Claude Code 审核 (安全 + 契约)
5. 审核通过后, 在嘉立创下单打样 (5 片最便宜档)
