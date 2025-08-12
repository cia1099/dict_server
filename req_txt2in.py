# convert_requirements.py
import re
import sys
from pathlib import Path

if len(sys.argv) != 2:
    print(f"用法: python {Path(__file__).name} <requirements.txt 路径>")
    sys.exit(1)

input_path = Path(sys.argv[1])

if not input_path.is_file():
    print(f"错误: 找不到文件 {input_path}")
    sys.exit(1)

# 自动生成输出路径 (同目录，替换扩展名为 .in)
output_path = input_path.with_suffix(".in")

with open(input_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

result = []
for line in lines:
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    # 去掉版本号部分
    pkg = re.split(r"[=<>!~]", line, 1)[0].strip()
    if pkg:
        result.append(pkg)

# 去重 + 排序
result = sorted(set(result), key=str.lower)

with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n".join(result))

print(f"✅ 已生成 {output_path}，共 {len(result)} 个顶层依赖。")
