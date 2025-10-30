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
    print("🧪 Qsys 自动化测试选择")
    print("=" * 50)

    print("选择测试类型:")
    print("1. 独立规则测试 (推荐，无Streamlit依赖)")
    print("2. 完整回测测试 (需要Streamlit环境)")
    print("3. 单规则测试 (需要Streamlit环境)")

    try:
        choice = input("\n请选择 (1/2/3): ").strip()

        if choice == '1':
            print("\n🚀 启动独立规则测试...")
            from test_rule_standalone import main as run_standalone_test
            run_standalone_test()

        elif choice == '2':
            print("\n🚀 启动完整回测测试...")
            print("注意: 需要Streamlit环境")
            from tests.automation.test_backtest_automation import main as run_tests
            asyncio.run(run_tests())

        elif choice == '3':
            print("\n🚀 启动单规则测试...")
            print("注意: 需要Streamlit环境")
            from test_single_rule import main as run_single_test
            run_single_test()

        else:
            print("❌ 无效选择")
            sys.exit(1)

    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("💡 建议: 使用选项1 - 独立规则测试")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 测试已取消")
    except Exception as e:
        print(f"❌ 运行错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()