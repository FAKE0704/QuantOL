#!/usr/bin/env python3
"""
自动化测试运行器
快速运行回测测试套件的便捷脚本
"""

import os
import sys
import asyncio
from pathlib import Path

# 确保项目根目录在Python路径中
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """运行自动化测试"""
    print("🧪 Qsys 自动化回测测试")
    print("=" * 50)

    try:
        # 导入并运行测试
        from tests.automation.test_backtest_automation import main as run_tests
        asyncio.run(run_tests())

    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保所有依赖模块已正确安装")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 运行错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()