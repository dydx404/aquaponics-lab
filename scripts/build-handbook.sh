#!/usr/bin/env bash
# 把 docs/handbook 的 Markdown 合并导出为一本带目录的 PDF。
# 依赖：pandoc + xelatex（TeX Live / MiKTeX），并安装中文字体（如 Noto Sans CJK SC）。
set -euo pipefail

HB_DIR="$(cd "$(dirname "$0")/../docs/handbook" && pwd)"
OUT="${1:-aquaponics-lab-handbook.pdf}"
CJK_FONT="${CJK_FONT:-Noto Sans CJK SC}"

cd "$HB_DIR"
# 章节按数字顺序，README 作为封面/前置
FILES=$(ls [0-9]*.md | sort)

pandoc README.md $FILES \
  -o "$OUT" \
  --toc --toc-depth=2 --number-sections \
  -V documentclass=report \
  -V geometry:margin=2.5cm \
  -V CJKmainfont="$CJK_FONT" \
  -V linkcolor=blue \
  --pdf-engine=xelatex

echo "已生成：$HB_DIR/$OUT"
