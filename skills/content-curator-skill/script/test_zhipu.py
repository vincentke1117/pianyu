#!/usr/bin/env python3
"""测试 zhipu-cli 返回的数据结构"""

import os
import sys
import json
import subprocess
import re

# 设置 UTF-8 编码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def remove_ansi_codes(text: str) -> str:
    """去除字符串中的 ANSI 转义序列"""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

# 读取 .env 文件
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, "dist", ".env")
env = os.environ.copy()

if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                if key.strip() == 'ZHIPU_API_KEY':
                    env['ZHIPU_API_KEY'] = value.strip()
                    break

# 测试 URL
test_url = "https://karpathy.bearblog.dev/chemical-hygiene/"

zhipu_cli = os.path.join(script_dir, "dist", "zhipu-cli.exe" if sys.platform == "win32" else "zhipu-cli")

print(f"测试 URL: {test_url}")
print(f"zhipu-cli 路径: {zhipu_cli}")
print()

# 调用 zhipu-cli
result = subprocess.run(
    [zhipu_cli, "read", test_url],
    capture_output=True,
    text=True,
    timeout=60,
    encoding='utf-8',
    env=env
)

if result.returncode != 0:
    print(f"错误: {result.stderr}")
    sys.exit(1)

# 去除 ANSI 代码
content = remove_ansi_codes(result.stdout.strip())

print("=" * 60)
print("原始输出（前500字符）:")
print("=" * 60)
try:
    print(content[:500])
except UnicodeEncodeError:
    print(content[:500].encode('utf-8', errors='replace').decode('utf-8'))
print()

# 尝试解析 JSON
try:
    article_data = json.loads(content)
    print("=" * 60)
    print("JSON 结构:")
    print("=" * 60)
    json_str = json.dumps(article_data, indent=2, ensure_ascii=False)[:2000]
    try:
        print(json_str)
    except UnicodeEncodeError:
        print(json_str.encode('utf-8', errors='replace').decode('utf-8'))
    print()
    print("=" * 60)
    print("顶层键:")
    print("=" * 60)
    print(list(article_data.keys()))

    if "text" in article_data:
        text_data = article_data["text"]
        print()
        print("=" * 60)
        print("text 中的键:")
        print("=" * 60)
        print(list(text_data.keys()))

        if "metadata" in text_data:
            metadata = text_data["metadata"]
            print()
            print("=" * 60)
            print("metadata 中的键:")
            print("=" * 60)
            print(list(metadata.keys()))
            print()
            print("=" * 60)
            print("metadata 内容（前1000字符）:")
            print("=" * 60)
            metadata_str = json.dumps(metadata, indent=2, ensure_ascii=False)[:1000]
            try:
                print(metadata_str)
            except UnicodeEncodeError:
                print(metadata_str.encode('utf-8', errors='replace').decode('utf-8'))

except json.JSONDecodeError as e:
    print(f"不是 JSON 格式: {e}")
