"""
测试插件加载

作者: AI架构团队
版本: 1.0.0
日期: 2026-04-04
"""

import importlib
import os
from pathlib import Path

# 测试插件加载
plugins_dir = "src/plugins"
plugins_path = Path(plugins_dir)

print(f"插件目录: {plugins_path}")
print(f"目录存在: {plugins_path.exists()}")

if plugins_path.exists():
    print("\n插件目录内容:")
    for root, dirs, files in os.walk(plugins_path):
        level = root.replace(str(plugins_path), '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            if file.endswith('.py'):
                print(f"{subindent}{file}")

# 测试模块导入
try:
    from plugins.strategies.keyword_strategy import KeywordStrategy
    print("\n✓ 成功导入 KeywordStrategy")
except Exception as e:
    print(f"\n✗ 导入 KeywordStrategy 失败: {e}")

try:
    from plugins.handlers.chat_handler import ChatHandler
    print("✓ 成功导入 ChatHandler")
except Exception as e:
    print(f"✗ 导入 ChatHandler 失败: {e}")
