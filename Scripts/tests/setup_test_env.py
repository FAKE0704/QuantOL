#!/usr/bin/env python3
"""
测试环境设置脚本

设置正确的Python路径以便测试能够正常运行
"""

import os
import sys
from pathlib import Path

def setup_test_environment():
    """设置测试环境"""
    # 获取项目根目录
    project_root = Path(__file__).parent.parent.parent

    # 添加项目根目录到Python路径
    sys.path.insert(0, str(project_root))

    # 设置环境变量
    os.environ['PYTHONPATH'] = str(project_root) + os.pathsep + os.environ.get('PYTHONPATH', '')

    print(f"✅ 测试环境已设置")
    print(f"   项目根目录: {project_root}")
    print(f"   Python路径: {sys.path[0]}")

    return project_root

def verify_imports():
    """验证关键模块是否可以导入"""
    print("\n🔍 验证模块导入...")

    modules_to_test = [
        "src.core.strategy.rule_parser",
        "src.support.log.logger",
        "src.core.data.database"
    ]

    for module_path in modules_to_test:
        try:
            __import__(module_path)
            print(f"   ✅ {module_path}")
        except ImportError as e:
            print(f"   ❌ {module_path}: {e}")

def main():
    """主函数"""
    print("🚀 设置测试环境")
    print("=" * 50)

    project_root = setup_test_environment()
    verify_imports()

    print("\n🎉 环境设置完成")

if __name__ == "__main__":
    main()